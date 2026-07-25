
from src.core.imports import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Processor:
    def __init__(self):
        self.dl_map = json.load(open("map/dl_map.json", encoding="utf-8"))
        self.ws_map = json.load(open("map/ws_map.json", encoding="utf-8"))

    def _load_spider(self, module_path, class_name):
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
       
    def run_listing_category(self, listing_data):
        website_key = listing_data['website'].lower()   # KEEP www.

        config = self.dl_map.get(website_key)
        if not config:
            raise ValueError(f"No dl_map spider for {website_key}")

        SpiderClass = self._load_spider(
            config["module"],
            config["class"]
        )

        spider = SpiderClass(
            website=listing_data['website'],
            country=listing_data['country'],
            url=listing_data['url'],
        )

        logging.info("Running LISTING spider")
        return spider.get_category_urls()

    def run_listing_products(self, listing_data, category_data):
        website_key = listing_data["website"].lower()

        config = self.dl_map.get(website_key)
        if not config:
            raise ValueError(f"No dl_map spider for {website_key}")

        SpiderClass = self._load_spider(
            config["module"],
            config["class"]
        )

        spider = SpiderClass(
            website=listing_data["website"],
            country=listing_data["country"],
            url=listing_data["url"],
        )

        logging.info("Running PRODUCT URL spider")

        return spider.get_product_urls(category_data)

    def run_website(self, listing_data, product_data):

        website_key = listing_data["website"].lower()

        config = self.ws_map.get(website_key)

        if not config:
            raise ValueError(f"No ws_map spider for {website_key}")

        SpiderClass = self._load_spider(
            config["module"],
            config["class"]
        )

        spider = SpiderClass(
            website=listing_data["website"],
            country=listing_data["country"],
            url=listing_data["url"]
        )

        logger.info("Running WEBSITE spider")

        return spider.parse_items(product_data)