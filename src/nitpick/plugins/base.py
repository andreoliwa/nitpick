"""Base class for file checkers."""
import abc
from typing import TYPE_CHECKING, Optional, Set, Type

import jmespath

from nitpick.app import Nitpick
from nitpick.formats import TomlFormat
from nitpick.generic import get_subclasses, search_dict
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import JsonDict, YieldFlake8Error

if TYPE_CHECKING:
    from pathlib import Path
    from marshmallow import Schema


class BaseFile(NitpickMixin, metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    file_name = ""
    error_base_number = 300

    #: Nested validation field for this file, to be applied in runtime when the validation schema is rebuilt.
    #: Useful when you have a strict configuration for a file type (e.g. :py:class:`nitpick.plugins.json.JSONFile`).
    nested_field = None  # type: Optional[Schema]

    fixed_name_classes = set()  # type: Set[Type[BaseFile]]
    dynamic_name_classes = set()  # type: Set[Type[BaseFile]]

    #: Which :py:package:`identify` tags this :py:class:`nitpick.files.base.BaseFile` child recognises.
    identify_tags = set()  # type: Set[str]

    def __init__(self, config: JsonDict, file_name: str = None) -> None:
        if file_name is not None:
            self.file_name = file_name

        self.error_prefix = "File {}".format(self.file_name)
        self.file_path = Nitpick.current_app().root_dir / self.file_name  # type: Path

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict = config or {}  # type: JsonDict

        # Nitpick configuration for this file as a TOML dict, taken from the style file.
        self.nitpick_file_dict = search_dict(
            'files."{}"'.format(self.file_name), Nitpick.current_app().config.nitpick_section, {}
        )  # type: JsonDict

    @classmethod
    def load_fixed_dynamic_classes(cls) -> None:
        """Separate classes with fixed file names from classes with dynamic files names."""
        cls.fixed_name_classes = set()
        cls.dynamic_name_classes = set()
        for subclass in get_subclasses(BaseFile):
            if subclass.file_name:
                cls.fixed_name_classes.add(subclass)
            else:
                cls.dynamic_name_classes.add(subclass)

    @classmethod
    def get_compiled_jmespath_file_names(cls):
        """Return a compiled JMESPath expression for file names, using the class name as part of the key."""
        return jmespath.compile("nitpick.{}.file_names".format(cls.__name__))

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist."""
        config_data_exists = bool(self.file_dict or self.nitpick_file_dict)
        should_exist = Nitpick.current_app().config.nitpick_files_section.get(
            TomlFormat.group_name_for(self.file_name), True
        )  # type: bool
        file_exists = self.file_path.exists()

        if config_data_exists and not file_exists:
            suggestion = self.suggest_initial_contents()
            phrases = [" was not found"]
            message = Nitpick.current_app().config.nitpick_files_section.get(self.file_name)
            if message and isinstance(message, str):
                phrases.append(message)
            if suggestion:
                phrases.append("Create it with this content:")
            yield self.flake8_error(1, ". ".join(phrases), suggestion)
        elif not should_exist and file_exists:
            # Only display this message if the style is valid.
            if not Nitpick.current_app().style_errors:
                yield self.flake8_error(2, " should be deleted")
        elif file_exists and config_data_exists:
            yield from self.check_rules()

    @abc.abstractmethod
    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited classes if needed."""

    @abc.abstractmethod
    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
