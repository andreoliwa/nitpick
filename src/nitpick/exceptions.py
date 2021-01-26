"""Nitpick exceptions."""
import warnings
from pathlib import Path
from typing import Any, Dict

import click

from nitpick.constants import ERROR_PREFIX, PROJECT_NAME
from nitpick.typedefs import Flake8Error


class NitpickError(Exception):
    """A Nitpick error  raise flake8 errors."""

    error_base_number: int = 0
    error_prefix: str = ""
    message: str = ""
    number: int = 0
    add_to_base_number: bool = True

    def __init__(self, message: str = "", suggestion: str = "", number: int = 0, add_to_base_number=True) -> None:
        self.message: str = message or self.message
        self.suggestion: str = suggestion
        if number:
            self.number = number
        self.add_to_base_number = add_to_base_number

        super().__init__(self.message)

    def as_flake8_warning(self) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        joined_number = self.error_base_number + self.number if self.add_to_base_number else self.number
        suggestion_with_newline = (
            click.style("\n{}".format(self.suggestion.rstrip()), fg="green") if self.suggestion else ""
        )

        from nitpick.flake8 import NitpickExtension  # pylint: disable=import-outside-toplevel

        return (
            0,
            0,
            "{}{:03d} {}{}{}".format(
                ERROR_PREFIX, joined_number, self.error_prefix, self.message.rstrip(), suggestion_with_newline
            ),
            NitpickExtension,
        )


class InitError(NitpickError):
    """Init errors."""

    error_base_number = 100


class NoRootDirError(InitError):
    """No root dir found."""

    number = 1
    message = "No root dir found (is this a Python project?)"


class NoPythonFileError(InitError):
    """No Python file was found."""

    number = 2
    message = "No Python file was found on the root dir and subdir of {!r}"

    def __init__(self, root_dir: Path, **kwargs) -> None:
        self.message = self.message.format(str(root_dir))
        super().__init__(self.message, **kwargs)


class PresentFileError(InitError):
    """File exists when it shouldn't."""

    number = 3


class AbsentFileError(InitError):
    """File doesn't exist when it should."""

    number = 4


class ConfigError(NitpickError):
    """Config error."""

    error_base_number = 200


class MinimumVersionError(ConfigError):
    """Warn about minimum Nitpick version."""

    number = 3
    message = "The style file you're using requires {project}>={expected} (you have {actual}). Please upgrade"

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(self.message.format(project=PROJECT_NAME, expected=expected, actual=actual))


class StyleError(NitpickError):
    """An error in a style file."""

    number = 1
    add_to_base_number = False

    def __init__(self, style_file_name: str, message: str = "", suggestion: str = "", **kwargs) -> None:
        message = f"File {style_file_name} has an incorrect style. {message}"
        super().__init__(message, suggestion, **kwargs)


class PluginError(NitpickError):
    """Base for plugin errors."""

    error_base_number = 300


class Deprecation:
    """All deprecation messages in a single class.

    When it's time to break compatibility, remove a method/warning below,
    and older config files will trigger validation errors on Nitpick.
    """

    @staticmethod
    def pre_commit_without_dash(path_from_root: str) -> bool:
        """The pre-commit config should start with a dot on the config file."""
        from nitpick.plugins.pre_commit import PreCommitPlugin  # pylint: disable=import-outside-toplevel

        if path_from_root == PreCommitPlugin.file_name[1:]:
            warnings.warn(
                'The section name for dotfiles should start with a dot: [".{}"]'.format(path_from_root),
                DeprecationWarning,
            )
            return True

        return False

    @staticmethod
    def jsonfile_section(style_errors: Dict[str, Any], is_merged_style: bool) -> bool:
        """The [nitpick.JSONFile] is not needed anymore; JSON files are now detected by the extension."""
        has_nitpick_jsonfile_section = style_errors.get(PROJECT_NAME, {}).pop("JSONFile", None)
        if has_nitpick_jsonfile_section:
            if not style_errors[PROJECT_NAME]:
                style_errors.pop(PROJECT_NAME)
            if not is_merged_style:
                warnings.warn(
                    "The [nitpick.JSONFile] section is not needed anymore; just declare your JSON files directly",
                    DeprecationWarning,
                )
                return True
        return False
