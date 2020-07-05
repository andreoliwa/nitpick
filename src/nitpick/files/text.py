"""Text files."""
import logging
from typing import Optional, Set

from nitpick.files.base import BaseFile
from nitpick.plugin import NitpickPlugin, hookimpl
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


class TextPlugin(NitpickPlugin):  # pylint: disable=too-few-public-methods
    """Handle text files."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle text files."""
        self.base_file = TextFile(filename)
        return self if "plain-text" in tags else None
