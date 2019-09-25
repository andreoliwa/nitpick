"""Base class for file checkers."""
import abc
from typing import TYPE_CHECKING, Generator, List, Optional, Set, Type

import jmespath

from nitpick import Nitpick
from nitpick.formats import TomlFormat
from nitpick.generic import get_subclasses, search_dict
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import YieldFlake8Error

if TYPE_CHECKING:
    from pathlib import Path
    from marshmallow import Schema
    from nitpick.typedefs import JsonDict  # pylint: disable=ungrouped-imports


class BaseFile(NitpickMixin, metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    has_multiple_files = False
    file_name = ""
    error_base_number = 300

    error_prefix = ""
    file_path = None  # type: Path
    file_dict = {}  # type: JsonDict
    nitpick_file_dict = {}  # type: JsonDict

    #: Nested validation field for this file, to be applied in runtime when the validation schema is rebuilt.
    #: Useful when you have a strict configuration for a file type (e.g. :py:class:`nitpick.files.json.JSONFile`).
    nested_field = None  # type: Optional[Schema]

    fixed_name_classes = set()  # type: Set[Type[BaseFile]]
    dynamic_name_classes = set()  # type: Set[Type[BaseFile]]

    def __init__(self) -> None:
        if self.has_multiple_files:
            key = "{}.file_names".format(self.__class__.__name__)
            self._multiple_files = search_dict(key, Nitpick.current_app().config.nitpick_section, [])  # type: List[str]
        else:
            self._multiple_files = [self.file_name]
            self._set_current_data(self.file_name)

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

    def _set_current_data(self, file_name: str) -> None:
        """Set data for the current file name, either if there are multiple or single files."""
        if self.has_multiple_files:
            self.file_name = file_name

        self.error_prefix = "File {}".format(self.file_name)
        self.file_path = Nitpick.current_app().root_dir / self.file_name

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict = Nitpick.current_app().config.style_dict.get(TomlFormat.group_name_for(self.file_name), {})

        # Nitpick configuration for this file as a TOML dict, taken from the style file.
        self.nitpick_file_dict = search_dict(
            'files."{}"'.format(self.file_name), Nitpick.current_app().config.nitpick_section, {}
        )

    @classmethod
    def get_compiled_jmespath_file_names(cls):
        """Return a compiled JMESPath expression for file names, using the class name as part of the key."""
        return jmespath.compile("nitpick.{}.file_names".format(cls.__name__))

    @property
    def multiple_files(self) -> Generator:
        """Yield the next multiple file, one by one."""
        for file_name in self._multiple_files:
            self._set_current_data(file_name)
            yield file_name

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist."""
        for _ in self.multiple_files:
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
