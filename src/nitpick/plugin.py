"""Flake8 plugin to check files."""
from typing import TYPE_CHECKING, Any, Dict, Optional, Set

import pluggy

from nitpick.constants import PROJECT_NAME

if TYPE_CHECKING:
    from nitpick.files.base import BaseFile


hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)


@hookspec
def handle_config_file(  # pylint: disable=unused-argument
    filename: str, tags: Set[str], config_dict: Dict[str, Any]
) -> Optional["BaseFile"]:
    """Return a BaseFile if this plugin handles the relative filename or any of its :py:package:`identify` tags."""
