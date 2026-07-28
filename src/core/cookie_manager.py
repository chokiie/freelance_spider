from pathlib import Path
from core.file_manager import FileManager
from core.logger import logger

class CookieManager:
    """
    Handles persistent cookies for download strategies.
    """
    def __init__(self,website,country):
        self.website = website
        self.country = country
        self.file_manager = FileManager()
        self.cookie_path = (Path("cookies")/country/f"{website}.json")

    def exists(self):
        """
        Returns True if a cookie file exists.
        """
        return self.cookie_path.exists()

    def load(self):
        """
        Load cookies from disk.
        """
        if not self.exists():
            logger.info("No cookie file found.")
            return {}
        return self.file_manager.load_json(self.cookie_path)

    def save(self,cookies):
        """
        Save cookies to disk.
        """
        self.file_manager.save_json(self.cookie_path,cookies)
        logger.info("Cookies saved.")

    def delete(self):
        """
        Delete stored cookies.
        """
        if self.exists():
            self.cookie_path.unlink()
            logger.info("Cookies deleted.")