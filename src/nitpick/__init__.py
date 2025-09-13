"""Main module."""

from loguru import logger

from nitpick.constants import PROJECT_NAME
from nitpick.core import Nitpick

__all__ = ("Nitpick",)
__version__ = "0.36.0"

logger.disable(PROJECT_NAME)
