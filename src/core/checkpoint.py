from pathlib import Path
import threading
from core.logger import logger
from core.file_manager import FileManager


class Checkpoint:
    """
    Thread-safe checkpoint manager.

    Responsibilities
    ----------------
    - Resume interrupted spiders
    - Track page progress
    - Track item counts
    - Track failed categories
    """

    def __init__(self,website,country):
        self.website = website
        self.country = country
        self.file_manager = FileManager()
        # Reentrant lock avoids deadlocks when one checkpoint
        # method calls another checkpoint method.
        self.lock = threading.RLock()
        self.folder = Path("checkpoint")
        filename = (f"{website}_{country}.json".replace(".", "_"))
        self.file = self.folder / filename
        self.data = {
            "website": website,
            "country": country,
            "categories": {},
            "failed": []}
        self.load()

    ##################################################
    # Load
    ##################################################

    def load(self):
        if not self.file.exists():
            return
        try:
            data = self.file_manager.load_json(self.file)
            if data:
                self.data = data
            logger.info("Checkpoint loaded: %s",self.file)
        except Exception:
            logger.exception("Failed loading checkpoint.")

    ##################################################
    # Save
    ##################################################

    def save(self):
        with self.lock:
            try:
                self.file_manager.save_json(self.file,self.data)
            except Exception:
                logger.exception("Failed saving checkpoint.")

    ##################################################
    # Ensure Category Exists
    ##################################################

    def create_category(self,category):
        with self.lock:
            if category in self.data["categories"]:
                return
            self.data["categories"][category] = {
                "status": "running","last_completed_page": -1,"items": 0}
            self.save()

    ##################################################
    # Update Progress
    ##################################################

    def update_progress(self,category,page,items):
        with self.lock:
            self.create_category(category)
            info = self.data["categories"][category]
            info["last_completed_page"] = page
            info["items"] += items
            self.save()

    ##################################################
    # Completed
    ##################################################

    def mark_completed(self,category):
        with self.lock:
            self.create_category(category)
            self.data["categories"][category]["status"] = "completed"
            self.save()

    ##################################################
    # Failed
    ##################################################

    def mark_failed(self,category,url,error):
        with self.lock:
            self.create_category(category)
            self.data["categories"][category]["status"] = "failed"
            self.data["failed"].append({
                "category": category,"url": url,"error": str(error)})
            self.save()

    ##################################################
    # Resume Page
    ##################################################

    def get_resume_page(self,category):
        with self.lock:
            if category not in self.data["categories"]:
                return 0
            return (
                self.data["categories"][category]
                .get("last_completed_page",-1)+ 1)

    ##################################################
    # Category Completed?
    ##################################################

    def is_completed(self,category):
        with self.lock:
            if category not in self.data["categories"]:
                return False
            return (
                self.data["categories"][category]["status"]
                == "completed")

    ##################################################
    # Reset Checkpoint
    ##################################################

    def reset(self):
        with self.lock:
            self.data = {
                "website": self.website,
                "country": self.country,
                "categories": {},
                "failed": []}
            self.save()