"""Nitpick exceptions."""
import warnings
from pathlib import Path
from typing import Any, Dict

from nitpick.constants import PROJECT_NAME


class NitpickError(Exception):
    """A Nitpick error  raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str

    number = 0  # type: int
    message = ""  # type: str
    suggestion = None  # type: str
    add_to_base_number = True

    def __init__(self, *args: object) -> None:
        if not args:
            super().__init__(self.message)
        else:
            super().__init__(*args)


class PluginError(NitpickError):
    """Plugin error."""

    error_base_number = 100


class NoRootDir(PluginError):
    """No root dir found."""

    number = 1
    message = "No root dir found (is this a Python project?)"


class NoPythonFile(PluginError):
    """No Python file was found."""

    number = 2
    message = "No Python file was found on the root dir and subdir of {!r}"

    def __init__(self, root_dir: Path, *args: object) -> None:
        self.message = self.message.format(str(root_dir))
        super().__init__(self.message, *args)


class StyleError(NitpickError):
    """An error in a style file."""

    number = 1
    add_to_base_number = False

    def __init__(self, style_file_name: str, *args: object) -> None:
        self.style_file_name = style_file_name
        super().__init__(*args)


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
