from core.http_client import HttpClient
from core.checkpoint import Checkpoint
from core.logger import logger
from core.config import CATEGORY_RETRY_COUNT,MAX_CATEGORY_THREADS
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from core.exceptions import (APIError)
from src.core.cookie_manager import CookieManager
from src.core.proxy_manager import ProxyManager
import time, threading

class BaseDownloadStrategy:
    def __init__(self,website,country,url):
        self.proxy_manager = ProxyManager()
        self.website = website
        self.country = country
        self.url = url
        self.client = HttpClient()
        self.checkpoint = Checkpoint(website,country)
        self.failed_categories = []
        self.failed_lock = threading.Lock()
        self.start_time = time.time()
        self.cookie_manager = CookieManager(website,country)
        self.cookies = self.cookie_manager.load()
        self.metrics = {"get_requests": 0,"post_requests": 0,"successful_requests": 0,"failed_requests": 0,"total_response_time": 0.0,}
    def before_request(self, method, url, **kwargs):
        """
        Hook executed before every request.
        Child classes may override this.
        """
        pass

    def after_request(self, method, url, response):
        """
        Hook executed after every successful request.
        Child classes may override this.
        """
        pass

    def get(self, url, **kwargs):
        """
        Wrapper for HTTP GET requests.
        """
        logger.debug("GET %s", url)
        cookies = self.cookies
        proxy = self.proxy_manager.get_proxy()
        self.metrics["get_requests"] += 1
        start = time.perf_counter()
        try:
            self.before_request("GET",url,**kwargs)
            response = self.client.get(url, proxy=proxy, cookies=cookies,**kwargs)
            self.after_request("GET",url,response)
            self.metrics["successful_requests"] += 1
            return response
        except Exception:
            self.metrics["failed_requests"] += 1
            raise
        finally:
            elapsed = time.perf_counter() - start
            self.metrics["total_response_time"] += elapsed

    def post(self, url, **kwargs):
        """
        Wrapper for HTTP POST requests.
        """
        logger.debug("POST %s", url)
        cookies = self.cookies
        proxy = self.proxy_manager.get_proxy()
        self.metrics["post_requests"] += 1
        start = time.perf_counter()
        try:
            self.before_request("POST",url,**kwargs)
            response = self.client.post(url, proxy=proxy, cookies=cookies,**kwargs)
            self.after_request("POST",url,response)
            self.metrics["successful_requests"] += 1
            return response
        except Exception:
            self.metrics["failed_requests"] += 1
            raise
        finally:
            elapsed = time.perf_counter() - start
            self.metrics["total_response_time"] += elapsed

    def get_soup(self, url, parser="html.parser", **kwargs):
        """
        Download a page and return a BeautifulSoup object.
        """
        response = self.get(url,**kwargs)
        return BeautifulSoup(response.text,parser)

    def post_json(self, url, error_message="Invalid JSON response.", **kwargs):
        """
        Send POST request and return JSON.
        """
        response = self.post(url,**kwargs)
        try:
            return response.json()
        except Exception as e:
            raise APIError(error_message) from e

    def get_json(self, url, error_message="Invalid JSON response.", **kwargs):
        """
        Send GET request and return JSON.
        """
        response = self.get(url,**kwargs)
        try:
            return response.json()
        except Exception as e:
            raise APIError(error_message) from e
        
    ##################################################
    # Failed Categories
    ##################################################

    def add_failed_category(self,category,url,error):
        with self.failed_lock:
            self.failed_categories.append({"category": category,"url": url,"error": str(error)})

    def process_category(self, category):
        category_name = category["name"]
        category_url = category["url"]
        if self.checkpoint.is_completed(category_name):
            logger.info("Skipping completed category: %s",category_name)
            return []
        last_error = None
        for attempt in range(CATEGORY_RETRY_COUNT):
            try:
                if attempt > 0:
                    logger.warning(
                        "Retrying category (%d/%d): %s",
                        attempt + 1,CATEGORY_RETRY_COUNT,category_name,)
                    time.sleep(2)
                result = self.get_category_product_urls(category)
                self.checkpoint.mark_completed(category_name)
                return result
            except Exception as e:
                last_error = e
                logger.exception("Attempt %d failed for %s",attempt + 1,category_name,)
        logger.error("Category permanently failed: %s",category_name,)
        self.add_failed_category(category_name,category_url,last_error)
        self.checkpoint.mark_failed(category_name,category_url,last_error)
        return []

    def collect_results(self, results):
        """
        Combine all thread results into one list.
        """
        product_data = []
        for category_result in results:
            product_data.extend(category_result)
        return product_data

    def get_product_urls(self,category_data):
        if not category_data:
            logger.warning("No categories found.")
            return {"products": [],"failed_categories": []}
        max_workers = min(len(category_data),MAX_CATEGORY_THREADS)
        logger.info("Processing %d categories using %d threads",len(category_data),max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.process_category,category_data))
        product_data = self.collect_results(results)
        self.log_summary(product_data)
        self.log_failed_categories()
        return {"products": product_data,"failed_categories": self.failed_categories}

    def get_category_urls(self):
        """
        Return all categories for the website.
        Must be implemented by child classes.
        """
        raise NotImplementedError("Child class must implement get_category_urls().")

    def get_category_product_urls(self, category):
        """
        Download all products/jobs for a category.
        Must be implemented by child classes.
        """
        raise NotImplementedError("Child class must implement get_category_product_urls().")

    def log_summary(self, product_data):
        """
        Log scraping summary.
        """
        logger.info("SCRAPING FINISHED")
        logger.info("Products Collected : %d",len(product_data))

    def log_failed_categories(self):
        """
        Log failed categories after scraping.
        """
        if self.failed_categories:
            logger.warning( "FAILED CATEGORIES (%d)",len(self.failed_categories))
            for item in self.failed_categories:
                logger.warning("Category : %s",item["category"])
                logger.warning("URL : %s",item["url"])
                logger.warning("Error : %s",item["error"])
        else:
            logger.info("No failed categories.")

    def log_request_metrics(self):
        total_requests = (self.metrics["get_requests"]+ self.metrics["post_requests"])
        elapsed_runtime = (time.time() - self.start_time)
        average_response = 0
        if total_requests:average_response = (self.metrics["total_response_time"]/ total_requests)
        success_rate = 0
        if total_requests:success_rate = (self.metrics["successful_requests"]/ total_requests) * 100
        logger.info("========== REQUEST METRICS ==========")
        logger.info("GET Requests      : %d", self.metrics["get_requests"])
        logger.info("POST Requests     : %d", self.metrics["post_requests"])
        logger.info("Total Requests    : %d", total_requests)
        logger.info("Successful        : %d", self.metrics["successful_requests"])
        logger.info("Failed            : %d", self.metrics["failed_requests"])
        logger.info("Success Rate      : %.2f%%", success_rate)
        logger.info("Average Response  : %.3f sec", average_response)
        logger.info("Runtime           : %.2f sec", elapsed_runtime)        
    ##################################################
    # Cleanup
    ##################################################
    
    def close(self):
        """
        Cleanup resources before shutting down.
        """
        self.cookie_manager.save(self.client.get_cookies())
        self.log_request_metrics()
        self.client.close()