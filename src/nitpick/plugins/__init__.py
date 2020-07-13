"""Hook specifications used by Nitpick plugins.

.. note::

    The hook specifications and the plugin classes are still experimental and considered as an internal API.
    They might change at any time; use at your own risk.
"""
from typing import TYPE_CHECKING, Optional, Set, Type

import pluggy

from nitpick.constants import PROJECT_NAME
from nitpick.typedefs import JsonDict

if TYPE_CHECKING:
    from nitpick.plugins.base import NitpickPlugin


hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)


@hookspec
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""


@hookspec
def handle_config_file(  # pylint: disable=unused-argument
    config: JsonDict, file_name: str, tags: Set[str]
) -> Optional["NitpickPlugin"]:
    """You should return a valid :py:class:`nitpick.plugins.base.NitpickPlugin` instance or ``None``.

    :return: A plugin instance if your plugin handles this file name or any of its ``identify`` tags.
        Return ``None`` if your plugin doesn't handle this file or file type.
    """
