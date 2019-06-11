# -*- coding: utf-8 -*-
"""Checker for the `pyproject.toml <https://poetry.eustace.io/docs/pyproject/>`_ config file (`PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_)."""
from nitpick.files.base import BaseFile
from nitpick.typedefs import YieldFlake8Error


class PyProjectTomlFile(BaseFile):
    """Checker for the `pyproject.toml <https://poetry.eustace.io/docs/pyproject/>`_ config file (`PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_)."""

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        if not self.config.pyproject_toml:
            return

        comparison = self.config.pyproject_toml.compare_with_flatten(self.file_dict)
        if comparison.missing_format:
            yield self.flake8_error(
                1, " has missing values. Use this:\n{}".format(comparison.missing_format.reformatted)
            )
        if comparison.diff_format:
            yield self.flake8_error(
                2, " has different values. Use this:\n{}".format(comparison.diff_format.reformatted)
            )

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""