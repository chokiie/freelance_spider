from core.imports import *
from core.logger import logger

class Statistics:
    def __init__(self):
        self.start_time = datetime.now()

    def summary(self,website,country,categories,failed_categories,products,items,):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        logger.info("=" * 50)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 50)
        logger.info("Website            : %s", website)
        logger.info("Country            : %s", country)
        logger.info("Categories         : %d", categories)
        logger.info("Failed Categories  : %d", failed_categories)
        logger.info("Products           : %d", products)
        logger.info("Items Parsed       : %d", items)
        logger.info("Started            : %s", self.start_time)
        logger.info("Finished           : %s", end_time)
        logger.info("Duration           : %.2f seconds", duration)
        logger.info("=" * 50)