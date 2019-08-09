"""Checker for the `pyproject.toml <https://poetry.eustace.io/docs/pyproject/>`_ config file (`PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_)."""
from nitpick.files.base import BaseFile
from nitpick.typedefs import YieldFlake8Error


class PyProjectTomlFile(BaseFile):
    """Checker for the `pyproject.toml <https://poetry.eustace.io/docs/pyproject/>`_ config file (`PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_)."""

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        if self.config.pyproject_toml:
            comparison = self.config.pyproject_toml.compare_with_flatten(self.file_dict)
            yield from self.warn_missing_different(comparison)

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""
