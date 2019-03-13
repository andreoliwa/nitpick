"""Base class for file checkers."""
import abc
from pathlib import Path

from flake8_nitpick.generic import search_dict
from flake8_nitpick.mixin import NitpickMixin
from flake8_nitpick.types import JsonDict, YieldFlake8Error


class BaseFile(NitpickMixin, metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    file_name: str
    error_base_number = 300

    def __init__(self) -> None:
        """Init instance."""
        from flake8_nitpick.config import NitpickConfig

        self.config = NitpickConfig.get_singleton()
        self.error_prefix = f"File {self.file_name}"
        self.file_path: Path = self.config.root_dir / self.file_name

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict: JsonDict = self.config.style_dict.get(self.toml_key(), {})

        # Nitpick configuration for this file as a TOML dict, taken from the style file.
        self.nitpick_file_dict: JsonDict = search_dict(f'files."{self.file_name}"', self.config.nitpick_dict, {})

    @classmethod
    def toml_key(cls):
        """Remove the dot in the beginning of the file name, otherwise it's an invalid TOML key."""
        return cls.file_name.lstrip(".")

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist; if there is style configuration for the file, then it should exist.

        The file should exist when there is any rule configured for it in the style file,
        TODO: add this to the docs
        """
        should_exist: bool = self.config.files.get(self.toml_key(), bool(self.file_dict or self.nitpick_file_dict))
        file_exists = self.file_path.exists()

        if should_exist and not file_exists:
            suggestion = self.suggest_initial_contents()
            phrases = [" was not found"]
            missing_message = self.nitpick_file_dict.get("missing_message", "")
            if missing_message:
                phrases.append(missing_message)
            if suggestion:
                phrases.append(f"Create it with this content:\n{suggestion}")
            yield self.flake8_error(1, ". ".join(phrases))
        elif not should_exist and file_exists:
            yield self.flake8_error(2, " should be deleted")
        elif file_exists:
            yield from self.check_rules()

    @abc.abstractmethod
    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited class if they need."""
        pass

    @abc.abstractmethod
    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        pass
