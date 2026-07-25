from core.imports import *
from src.core.config import (
    LOG_LEVEL,
    LOG_FORMAT
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

logger = logging.getLogger(__name__)