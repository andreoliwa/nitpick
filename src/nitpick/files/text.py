"""Text files."""
import logging

from nitpick.files.base import BaseFile
from nitpick.typedefs import YieldFlake8Error

LOGGER = logging.getLogger(__name__)


class TextFile(BaseFile):
    """Checker for any text file."""

    has_multiple_files = True
    error_base_number = 350

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""

    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited classes if needed."""
        return []
