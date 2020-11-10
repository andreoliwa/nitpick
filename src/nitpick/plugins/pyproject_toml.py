"""Checker for `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_."""
from typing import Optional, Set, Type

from nitpick.app import NitpickApp
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.typedefs import YieldFlake8Error


class PyProjectTomlPlugin(NitpickPlugin):
    """Checker for `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

    See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

    Example: :ref:`the Python 3.7 default <default-python-3-7>`.
    There are many other examples in :ref:`defaults`.
    """

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        if NitpickApp.current().config.pyproject_toml:
            comparison = NitpickApp.current().config.pyproject_toml.compare_with_flatten(self.file_dict)
            yield from self.warn_missing_different(comparison)

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return PyProjectTomlPlugin


@hookimpl
def handler(file_name: str, tags: Set[str]) -> Optional["NitpickPlugin"]:  # pylint: disable=unused-argument
    """Handle pyproject.toml file."""
    if file_name == PyProjectTomlPlugin.file_name:
        return PyProjectTomlPlugin()
    return None
