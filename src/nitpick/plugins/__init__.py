"""Hook specifications used by Nitpick plugins.

.. note::

    The hook specifications and the plugin classes are still experimental and considered as an internal API.
    They might change at any time; use at your own risk.
"""
from typing import TYPE_CHECKING, Optional, Type

import pluggy

from nitpick.constants import PROJECT_NAME

if TYPE_CHECKING:
    from nitpick.plugins.base import NitpickPlugin
    from nitpick.plugins.info import FileInfo

hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)

__all__ = ("hookspec", "hookimpl")


@hookspec
def plugin_class() -> Type["NitpickPlugin"]:
    """Return your plugin class here (it should inherit from :py:class:`nitpick.plugins.base.NitpickPlugin`)."""


@hookspec
def can_handle(info: "FileInfo") -> Optional[Type["NitpickPlugin"]]:  # pylint: disable=unused-argument
    """Return a valid :py:class:`nitpick.plugins.base.NitpickPlugin` instance or ``None``.

    :return: A plugin instance if your plugin handles this file info (path or any of its ``identify`` tags).
        Return ``None`` if your plugin doesn't handle this file or file type.
    """
