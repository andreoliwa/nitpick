"""Base class for file checkers."""
import abc
from typing import TYPE_CHECKING, Optional, Set, Type

import jmespath

from nitpick.app import NitpickApp
from nitpick.formats import TOMLFormat
from nitpick.generic import search_dict
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import JsonDict, YieldFlake8Error

if TYPE_CHECKING:
    from pathlib import Path

    from marshmallow import Schema


class NitpickPlugin(NitpickMixin, metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    file_name = ""
    error_base_number = 300

    #: Nested validation field for this file, to be applied in runtime when the validation schema is rebuilt.
    #: Useful when you have a strict configuration for a file type (e.g. :py:class:`nitpick.plugins.json.JSONPlugin`).
    validation_schema = None  # type: Optional[Schema]

    fixed_name_classes = set()  # type: Set[Type[NitpickPlugin]]
    dynamic_name_classes = set()  # type: Set[Type[NitpickPlugin]]

    # TODO: This info is duplicated. Use the value passed on the hook spec, and remove this attribute.
    #  For this to work, validation and dynamic schema have to be done in a different way
    #  (maybe NOT using dynamic schemas)
    #: Which ``identify`` tags this :py:class:`nitpick.plugins.base.NitpickPlugin` child recognises.
    identify_tags = set()  # type: Set[str]

    def __init__(self, config: JsonDict, file_name: str = None) -> None:
        if file_name is not None:
            self.file_name = file_name

        self.error_prefix = "File {}".format(self.file_name)
        self.file_path = NitpickApp.current().root_dir / self.file_name  # type: Path

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict = config or {}  # type: JsonDict

        # Nitpick configuration for this file as a TOML dict, taken from the style file.
        self.nitpick_file_dict = search_dict(
            'files."{}"'.format(self.file_name), NitpickApp.current().config.nitpick_section, {}
        )  # type: JsonDict

    @classmethod
    def load_fixed_dynamic_classes(cls) -> None:
        """Separate classes with fixed file names from classes with dynamic files names."""
        cls.fixed_name_classes = set()
        cls.dynamic_name_classes = set()
        for plugin_class in NitpickApp.current().plugin_manager.hook.plugin_class():
            if plugin_class.file_name:
                cls.fixed_name_classes.add(plugin_class)
            else:
                cls.dynamic_name_classes.add(plugin_class)

    @classmethod
    def get_compiled_jmespath_file_names(cls):
        """Return a compiled JMESPath expression for file names, using the class name as part of the key."""
        return jmespath.compile("nitpick.{}.file_names".format(cls.__name__))

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist."""
        config_data_exists = bool(self.file_dict or self.nitpick_file_dict)
        should_exist = NitpickApp.current().config.nitpick_files_section.get(
            TOMLFormat.group_name_for(self.file_name), True
        )  # type: bool
        file_exists = self.file_path.exists()

        if config_data_exists and not file_exists:
            suggestion = self.suggest_initial_contents()
            phrases = [" was not found"]
            message = NitpickApp.current().config.nitpick_files_section.get(self.file_name)
            if message and isinstance(message, str):
                phrases.append(message)
            if suggestion:
                phrases.append("Create it with this content:")
            yield self.flake8_error(1, ". ".join(phrases), suggestion)
        elif not should_exist and file_exists:
            # Only display this message if the style is valid.
            if not NitpickApp.current().style_errors:
                yield self.flake8_error(2, " should be deleted")
        elif file_exists and config_data_exists:
            yield from self.check_rules()

    @abc.abstractmethod
    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited classes if needed."""

    @abc.abstractmethod
    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
