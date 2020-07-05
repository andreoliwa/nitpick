"""Flake8 plugin to check files."""
from typing import TYPE_CHECKING, Optional, Set

import pluggy

from nitpick.constants import PROJECT_NAME

if TYPE_CHECKING:
    from nitpick.files.base import BaseFile


hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)


class NitpickPlugin:  # pylint: disable=too-few-public-methods
    """Base for a Nitpick plugin."""

    base_file = None  # type: BaseFile

    @hookspec
    def handle(self, filename: str, tags: Set[str]) -> Optional["NitpickPlugin"]:
        """Return self if this plugin handle the relative filename or any of its :py:package:`identify` tags."""
