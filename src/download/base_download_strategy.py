from src.core.imports import *

from src.core.http_client import HttpClient
from src.core.checkpoint import Checkpoint
from src.core.logger import logger


class BaseDownloadStrategy:
    """
    Base class for all download strategies.

    Shared responsibilities:

    - HTTP client
    - Checkpoint management
    - Failed category tracking
    - Thread synchronization
    """

    def __init__(
        self,
        website,
        country,
        url
    ):

        self.website = website
        self.country = country
        self.url = url

        self.client = HttpClient()

        self.checkpoint = Checkpoint(
            website,
            country
        )

        self.failed_categories = []

        self.failed_lock = threading.Lock()

    ##################################################
    # Failed Categories
    ##################################################

    def add_failed_category(
        self,
        category,
        url,
        error
    ):

        with self.failed_lock:

            self.failed_categories.append({

                "category": category,

                "url": url,

                "error": str(error)

            })

    ##################################################
    # Cleanup
    ##################################################

    def close(self):

        self.client.close()