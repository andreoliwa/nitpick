"""Text files."""
import logging
from typing import Optional, Set

from nitpick.plugins import hookimpl
from nitpick.plugins.base import BaseFile
from nitpick.typedefs import JsonDict, YieldFlake8Error

LOGGER = logging.getLogger(__name__)


class TextFile(BaseFile):
    """Checker for any text file."""

    error_base_number = 350

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""

    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited classes if needed."""
        return []


@hookimpl
def handle_config_file(  # pylint: disable=unused-argument
    config: JsonDict, file_name: str, tags: Set[str]
) -> Optional["BaseFile"]:
    """Handle text files."""
    return TextFile(config, file_name) if "plain-text" in tags else None
