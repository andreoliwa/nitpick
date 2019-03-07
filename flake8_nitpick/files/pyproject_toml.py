"""Checker for the pyproject.toml config file."""
import toml

from flake8_nitpick.files.base import BaseFile
from flake8_nitpick.generic import flatten, unflatten
from flake8_nitpick.types import YieldFlake8Error


class PyProjectTomlFile(BaseFile):
    """Check pyproject.toml."""

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        actual = flatten(self.config.pyproject_dict)
        expected = flatten(self.file_dict)
        if expected.items() <= actual.items():
            return

        missing_dict = unflatten({k: v for k, v in expected.items() if k not in actual})
        if missing_dict:
            missing_toml = toml.dumps(missing_dict)
            yield self.flake8_error(1, f" has missing values. Use this:\n{missing_toml}")

        diff_dict = unflatten({k: v for k, v in expected.items() if k in actual and expected[k] != actual[k]})
        if diff_dict:
            diff_toml = toml.dumps(diff_dict)
            yield self.flake8_error(2, f" has different values. Use this:\n{diff_toml}")
