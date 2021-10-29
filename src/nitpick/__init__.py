"""Main module."""
from loguru import logger

from nitpick.constants import PROJECT_NAME
from nitpick.core import Nitpick  # noqa: F401

__all__ = ("Nitpick",)
__version__ = "0.28.0"

logger.disable(PROJECT_NAME)
