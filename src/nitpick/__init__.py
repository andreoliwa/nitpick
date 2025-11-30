"""Main module."""

from loguru import logger

from nitpick.constants import PROJECT_NAME
from nitpick.core import Nitpick

__all__ = ("Nitpick",)
__version__ = "0.38.1"

logger.disable(PROJECT_NAME)
