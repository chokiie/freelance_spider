import json
import importlib

from src.core.logger import logger
from src.core.exceptions import ConfigurationError
from src.core.config import DEFAULT_ENCODING


class Processor:


    def __init__(self):

        self.dl_map = self._load_map(
            "map/dl_map.json"
        )

        self.ws_map = self._load_map(
            "map/ws_map.json"
        )


    ##################################################
    # Load JSON map
    ##################################################

    def _load_map(self, filepath):

        try:

            with open(
                filepath,
                encoding=DEFAULT_ENCODING
            ) as file:

                return json.load(file)


        except Exception as e:

            raise ConfigurationError(
                f"Failed loading map {filepath}: {e}"
            )


    ##################################################
    # Import Spider
    ##################################################

    def _load_spider(
        self,
        module_path,
        class_name
    ):

        try:

            module = importlib.import_module(
                module_path
            )

            return getattr(
                module,
                class_name
            )


        except Exception as e:

            raise ConfigurationError(
                f"Cannot load spider {class_name}: {e}"
            )


    ##################################################
    # Create Spider Instance
    ##################################################

    def _create_spider(
        self,
        config,
        listing_data
    ):

        SpiderClass = self._load_spider(
            config["module"],
            config["class"]
        )


        return SpiderClass(

            website=listing_data["website"],

            country=listing_data["country"],

            url=listing_data["url"]

        )


    ##################################################
    # Download Category
    ##################################################

    def run_listing_category(
        self,
        listing_data
    ):

        spider = self._get_download_spider(
            listing_data
        )


        logger.info(
            "Running CATEGORY spider"
        )


        return spider.get_category_urls()



    ##################################################
    # Download Products
    ##################################################

    def run_listing_products(
        self,
        listing_data,
        category_data
    ):

        spider = self._get_download_spider(
            listing_data
        )


        logger.info(
            "Running PRODUCT spider"
        )


        return spider.get_product_urls(
            category_data
        )



    ##################################################
    # Website Parser
    ##################################################

    def run_website(
        self,
        listing_data,
        product_data
    ):

        website_key = listing_data["website"].lower()


        config = self.ws_map.get(
            website_key
        )


        if not config:

            raise ConfigurationError(
                f"No website spider configured: {website_key}"
            )


        spider = self._create_spider(
            config,
            listing_data
        )


        logger.info(
            "Running WEBSITE spider"
        )


        return spider.parse_items(
            product_data
        )



    ##################################################
    # Helper
    ##################################################

    def _get_download_spider(
        self,
        listing_data
    ):

        website_key = listing_data["website"].lower()


        config = self.dl_map.get(
            website_key
        )


        if not config:

            raise ConfigurationError(
                f"No download spider configured: {website_key}"
            )


        return self._create_spider(
            config,
            listing_data
        )