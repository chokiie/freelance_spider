from src.core.imports import *
from src.core.processor import Processor
from exporter.json_exporter import JsonExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def run(static_data):

    processor = Processor()

    # --------------------------
    # Stage 1
    # --------------------------

    category_data = processor.run_listing_category(static_data)

    logger.info("Categories : %d", len(category_data))

    # --------------------------
    # Stage 2
    # --------------------------

    download_result = processor.run_listing_products(
        static_data,
        category_data
    )

    product_data = download_result["products"]
    failed_categories = download_result["failed_categories"]

    logger.info("Products : %d", len(product_data))
    logger.info("Failed Categories : %d", len(failed_categories))

    # --------------------------
    # Stage 3
    # --------------------------

    items = processor.run_website(
        static_data,
        product_data
    )

    logger.info("Items Parsed : %d", len(items))

    JsonExporter().save(
        jobs=items,
        static_data=static_data
    )
    
if __name__ == "__main__":

    static_data = {
        "website": "www.vietnamworks.com",
        "country": "vietnam",
        "url": "https://www.vietnamworks.com/job-search"
    }

    run(static_data)