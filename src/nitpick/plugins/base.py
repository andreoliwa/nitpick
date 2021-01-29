"""Base class for file checkers."""
import abc
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Optional, Set, Type

import jmespath
from identify import identify
from marshmallow import Schema

from nitpick.app import Nitpick
from nitpick.exceptions import Deprecation, NitpickError, PluginError
from nitpick.formats import Comparison
from nitpick.generic import search_dict
from nitpick.typedefs import JsonDict, mypy_property


class NitpickPlugin(metaclass=abc.ABCMeta):
    """Base class for file checkers."""

    file_name = ""
    error_class: Type[NitpickError] = PluginError

    #: Nested validation field for this file, to be applied in runtime when the validation schema is rebuilt.
    #: Useful when you have a strict configuration for a file type (e.g. :py:class:`nitpick.plugins.json.JSONPlugin`).
    validation_schema: Optional[Schema] = None

    #: Which ``identify`` tags this :py:class:`nitpick.plugins.base.NitpickPlugin` child recognises.
    identify_tags: Set[str] = set()

    skip_empty_suggestion = False

    def __init__(self, path_from_root: str = None) -> None:
        if path_from_root is not None:
            self.file_name = path_from_root

        self.error_class.error_prefix = "File {}".format(self.file_name)
        self.file_path: Path = Nitpick.create().project_root / self.file_name

        # Configuration for this file as a TOML dict, taken from the style file.
        self.file_dict: JsonDict = {}

    @mypy_property
    @lru_cache()
    def nitpick_file_dict(self) -> JsonDict:
        """Nitpick configuration for this file as a TOML dict, taken from the style file."""
        return search_dict(f'files."{self.file_name}"', Nitpick.create().config.nitpick_section, {})

    @classmethod
    def get_compiled_jmespath_file_names(cls):
        """Return a compiled JMESPath expression for file names, using the class name as part of the key."""
        return jmespath.compile("nitpick.{}.file_names".format(cls.__name__))

    def process(self, config: JsonDict) -> Iterator[NitpickError]:
        """Process the file, check if it should exist, check rules."""
        self.file_dict = config or {}

        config_data_exists = bool(self.file_dict or self.nitpick_file_dict)
        app = Nitpick.create()
        should_exist: bool = app.config.nitpick_files_section.get(self.file_name, True)
        file_exists = self.file_path.exists()

        if config_data_exists and not file_exists:
            suggestion = self.suggest_initial_contents()
            if not suggestion and self.skip_empty_suggestion:
                return
            phrases = [" was not found"]
            message = app.config.nitpick_files_section.get(self.file_name)
            if message and isinstance(message, str):
                phrases.append(message)
            if suggestion:
                phrases.append("Create it with this content:")
            joined_message = ". ".join(phrases)
            yield self.error_class(joined_message, suggestion, 1)
        elif not should_exist and file_exists:
            # Only display this message if the style is valid.
            yield self.error_class(" should be deleted", number=2)
        elif file_exists and config_data_exists:
            yield from self.check_rules()

    @abc.abstractmethod
    def check_rules(self) -> Iterator[NitpickError]:
        """Check rules for this file. It should be overridden by inherited classes if needed."""

    @abc.abstractmethod
    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""

    def warn_missing_different(self, comparison: Comparison, prefix_message: str = "") -> Iterator[NitpickError]:
        """Warn about missing and different keys."""
        # pylint: disable=not-callable
        if comparison.missing_format:
            yield self.error_class(f"{prefix_message} has missing values:", comparison.missing_format.reformatted, 8)
        if comparison.diff_format:
            yield self.error_class(
                f"{prefix_message} has different values. Use this:", comparison.diff_format.reformatted, 9
            )


class FilePathTags:  # pylint: disable=too-few-public-methods
    """Clean the file name and get its tags."""

    def __init__(self, path_from_root: str) -> None:
        if Deprecation.pre_commit_without_dash(path_from_root):
            self.path_from_root = "." + path_from_root
        else:
            self.path_from_root = "." + path_from_root[1:] if path_from_root.startswith("-") else path_from_root
        self.tags = set(identify.tags_from_filename(path_from_root))
