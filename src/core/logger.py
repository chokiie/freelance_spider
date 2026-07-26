import logging

from src.core.config import (
    LOG_LEVEL,
    LOG_FORMAT
)

def setup_logger():

    logger = logging.getLogger("freelance_spider")

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        LOG_FORMAT
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )

    logger.setLevel(
        getattr(
            logging,
            LOG_LEVEL
        )
    )

    logger.propagate = False

    return logger

logger = setup_logger()