"""Base class for file checkers."""
import abc
from pathlib import Path
from typing import Generator, List

from nitpick.generic import search_dict
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import JsonDict, YieldFlake8Error


class BaseFile(NitpickMixin, metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    has_multiple_files = False
    file_name = ""
    error_base_number = 300

    error_prefix = ""
    file_path = None  # type: Path
    file_dict = {}  # type: JsonDict
    nitpick_file_dict = {}  # type: JsonDict

    def __init__(self) -> None:
        """Init instance."""
        from nitpick.config import NitpickConfig

        self.config = NitpickConfig.get_singleton()
        if self.has_multiple_files:
            key = "{}.file_names".format(self.__class__.__name__)
            self._multiple_files = search_dict(key, self.config.nitpick_dict, [])  # type: List[str]
        else:
            self._multiple_files = [self.file_name]
            self._set_current_data(self.file_name)

    def _set_current_data(self, file_name: str) -> None:
        """Set data for the current file name, either if there are multiple or single files."""
        if self.has_multiple_files:
            self.file_name = file_name

        self.error_prefix = "File {}".format(self.file_name)
        self.file_path = self.config.root_dir / self.file_name

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict = self.config.style_dict.get(self.toml_key, {})

        # Nitpick configuration for this file as a TOML dict, taken from the style file.
        self.nitpick_file_dict = search_dict('files."{}"'.format(self.file_name), self.config.nitpick_dict, {})

    @property
    def toml_key(self) -> str:
        """Remove the dot in the beginning of the file name, otherwise it's an invalid TOML key."""
        return self.file_name.lstrip(".")

    @property
    def multiple_files(self) -> Generator:
        """Yield the next multiple file, one by one."""
        for file_name in self._multiple_files:
            self._set_current_data(file_name)
            yield file_name

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist; if there is style configuration for the file, then it should exist.

        The file should exist when there is any rule configured for it in the style file,
        TODO: add this to the docs
        """
        for _ in self.multiple_files:
            config_data_exists = bool(self.file_dict or self.nitpick_file_dict)
            should_exist = self.config.files.get(self.toml_key, True)  # type: bool
            file_exists = self.file_path.exists()

            if config_data_exists and not file_exists:
                suggestion = self.suggest_initial_contents()
                phrases = [" was not found"]
                missing_message = self.nitpick_file_dict.get("missing_message", "")
                if missing_message:
                    phrases.append(missing_message)
                if suggestion:
                    phrases.append("Create it with this content:")
                yield self.flake8_error(1, ". ".join(phrases), suggestion)
            elif not should_exist and file_exists:
                # Only display this message if the style is valid.
                if not self.config.has_style_errors:
                    yield self.flake8_error(2, " should be deleted")
            elif file_exists:
                yield from self.check_rules()

    @abc.abstractmethod
    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited classes if needed."""

    @abc.abstractmethod
    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
