"""Nitpick exceptions."""
import warnings
from typing import Any, Dict, List, Union

from more_itertools import always_iterable

from nitpick.constants import PROJECT_NAME
from nitpick.violations import Fuss


class QuitComplainingError(Exception):
    """Quit complaining and exit the application."""

    def __init__(self, violations: Union[Fuss, List[Fuss]]) -> None:
        super().__init__()
        self.violations: List[Fuss] = list(always_iterable(violations))


class Deprecation:
    """All deprecation messages in a single class.

    When it's time to break compatibility, remove a method/warning below,
    and older config files will trigger validation errors on Nitpick.
    """

    @staticmethod
    def pre_commit_without_dash(path_from_root: str) -> bool:
        """The pre-commit config should start with a dot on the config file."""
        from nitpick.plugins.pre_commit import PreCommitPlugin  # pylint: disable=import-outside-toplevel

        if path_from_root == PreCommitPlugin.filename[1:]:
            warnings.warn(
                f'The section name for dotfiles should start with a dot: [".{path_from_root}"]', DeprecationWarning
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


def pretty_exception(err: Exception, message: str = ""):
    """Return a pretty error message with the full path of the Exception."""
    return f"{message} ({err.__module__}.{err.__class__.__name__}: {str(err)})"
