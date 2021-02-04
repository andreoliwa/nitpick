"""Enforce config on `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_."""
from typing import Iterator, Optional, Type

from nitpick.constants import PYPROJECT_TOML
from nitpick.core import Nitpick
from nitpick.exceptions import NitpickError
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.data import FileData


class PyProjectTomlPlugin(NitpickPlugin):
    """Enforce config on `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

    See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

    Example: :ref:`the Python 3.7 default <default-python-3-7>`.
    There are many other examples in :ref:`defaults`.
    """

    filename = PYPROJECT_TOML
    violation_base_code = 310

    def enforce_rules(self) -> Iterator[NitpickError]:
        """Enforce rules for missing key/value pairs in pyproject.toml."""
        file = Nitpick.singleton().project.pyproject_toml
        if file:
            comparison = file.compare_with_flatten(self.file_dict)
            yield from self.warn_missing_different(comparison)

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return PyProjectTomlPlugin


@hookimpl
def can_handle(data: FileData) -> Optional["NitpickPlugin"]:
    """Handle pyproject.toml file."""
    if data.path_from_root == PYPROJECT_TOML:
        return PyProjectTomlPlugin(data)
    return None
