"""Base file checker."""
from pathlib import Path
from typing import Optional

from flake8_nitpick.types import YieldFlake8Error
from flake8_nitpick.utils import NitpickMixin


class BaseFile(NitpickMixin):
    """Base class for file checkers."""

    file_name: str
    error_base_number = 300
    missing_file_extra_message: Optional[str] = None

    def __init__(self) -> None:
        """Init instance."""
        from flake8_nitpick.config import NitpickConfig

        self.config = NitpickConfig.get_singleton()
        self.error_prefix = f"File: {self.file_name}: "
        self.file_path: Path = self.config.root_dir / self.file_name
        self.file_toml = self.config.style_toml.get(self.toml_key, {})

    @property
    def toml_key(self):
        """Remove the dot in the beginning of the file name, otherwise it's an invalid TOML key."""
        return self.file_name.lstrip(".")

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist; if there is style configuration for the file, then it should exist."""
        should_exist: bool = self.config.files.get(self.toml_key, bool(self.file_toml))
        file_exists = self.file_path.exists()

        if should_exist and not file_exists:
            suggestion = self.suggest_initial_file()
            phrases = ["Missing file"]
            if self.missing_file_extra_message:
                phrases.append(self.missing_file_extra_message)
            if suggestion:
                phrases.append(f"Suggested initial content:\n{suggestion}")
            yield self.flake8_error(1, ". ".join(phrases))
        elif not should_exist and file_exists:
            yield self.flake8_error(2, "File should be deleted")
        elif file_exists:
            for error in self.check_rules():
                yield error

    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited class if they need."""
        return []

    def suggest_initial_file(self) -> str:
        """Suggest the initial content for a missing file."""
        return ""
