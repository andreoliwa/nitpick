"""Checker for `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_."""
from typing import Optional, Set

from nitpick.app import Nitpick
from nitpick.plugins import hookimpl
from nitpick.plugins.base import BaseFile
from nitpick.typedefs import JsonDict, YieldFlake8Error


class PyProjectTomlFile(BaseFile):
    """Checker for `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

    See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

    Example: :ref:`the Python 3.7 default <default-python-3-7>`.
    There are many other examples in :ref:`defaults`.
    """

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        if Nitpick.current_app().config.pyproject_toml:
            comparison = Nitpick.current_app().config.pyproject_toml.compare_with_flatten(self.file_dict)
            yield from self.warn_missing_different(comparison)

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""


@hookimpl
def handle_config_file(  # pylint: disable=unused-argument
    config: JsonDict, file_name: str, tags: Set[str]
) -> Optional["BaseFile"]:
    """Handle pyproject.toml file."""
    base_file = PyProjectTomlFile(config)
    return base_file if file_name == base_file.file_name else None
