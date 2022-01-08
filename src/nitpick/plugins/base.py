"""Base class for file checkers."""
import abc
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, Optional, Set, Type

import jmespath
from autorepr import autotext
from loguru import logger
from marshmallow import Schema

from nitpick.constants import DUNDER_SEARCH_UNIQUE_KEY
from nitpick.documents import BaseDoc
from nitpick.generic import jmes_search_json
from nitpick.plugins.info import FileInfo
from nitpick.typedefs import JsonDict, mypy_property
from nitpick.violations import Fuss, Reporter, SharedViolations


class NitpickPlugin(metaclass=abc.ABCMeta):  # pylint: disable=too-many-instance-attributes
    """Base class for Nitpick plugins.

    :param data: File information (project, path, tags).
    :param expected_config: Expected configuration for the file
    :param autofix: Flag to modify files, if the plugin supports it (default: True).
    """

    __str__, __unicode__ = autotext("{self.info.path_from_root} ({self.__class__.__name__})")

    filename = ""  # TODO: remove filename attribute after fixing dynamic/fixed schema loading
    violation_base_code: int = 0

    #: Can this plugin modify its files directly? Are the files fixable?
    fixable: bool = False

    #: Nested validation field for this file, to be applied in runtime when the validation schema is rebuilt.
    #: Useful when you have a strict configuration for a file type (e.g. :py:class:`nitpick.plugins.json.JsonPlugin`).
    validation_schema: Optional[Schema] = None

    #: Which ``identify`` tags this :py:class:`nitpick.plugins.base.NitpickPlugin` child recognises.
    identify_tags: Set[str] = set()

    skip_empty_suggestion = False

    def __init__(self, info: FileInfo, expected_config: JsonDict, autofix=False) -> None:
        self.info = info
        self.filename = info.path_from_root
        self.reporter = Reporter(info, self.violation_base_code)

        self.file_path: Path = self.info.project.root / self.filename

        # Configuration for this file as a TOML dict, taken from the style file.
        self.expected_config: JsonDict = expected_config or {}

        self.autofix = self.fixable and autofix
        # Dirty flag to avoid changing files without need
        self.dirty: bool = False

        # The user can override the default unique keys (if any) by setting them on the style file.
        self.unique_keys: JsonDict = self.unique_keys_default.copy()
        self.unique_keys.update(self.expected_config.pop(DUNDER_SEARCH_UNIQUE_KEY, None) or {})

    @mypy_property
    @lru_cache()
    def nitpick_file_dict(self) -> JsonDict:
        """Nitpick configuration for this file as a TOML dict, taken from the style file."""
        return jmes_search_json(f'files."{self.filename}"', self.info.project.nitpick_section, {})

    @property
    def unique_keys_default(self) -> JsonDict:
        """Default unique keys that might be set by a plugin."""
        return {}

    @classmethod
    def get_compiled_jmespath_filenames(cls):
        """Return a compiled JMESPath expression for file names, using the class name as part of the key."""
        return jmespath.compile(f"nitpick.{cls.__name__}.filenames")

    def entry_point(self) -> Iterator[Fuss]:
        """Entry point of the Nitpick plugin."""
        self.post_init()

        should_exist: bool = bool(self.info.project.nitpick_files_section.get(self.filename, True))
        if self.file_path.exists() and not should_exist:
            logger.info(f"{self}: File {self.filename} exists when it should not")
            # Only display this message if the style is valid.
            yield self.reporter.make_fuss(SharedViolations.DELETE_FILE)
            return

        has_config_dict = bool(self.expected_config or self.nitpick_file_dict)
        if not has_config_dict:
            return

        yield from self._enforce_file_configuration()

    def _enforce_file_configuration(self):
        file_exists = self.file_path.exists()
        if file_exists:
            logger.info(f"{self}: Enforcing rules")
            yield from self.enforce_rules()
        else:
            yield from self._suggest_when_file_not_found()

        if self.autofix and self.dirty:
            fuss = self.write_file(file_exists)  # pylint: disable=assignment-from-none
            if fuss:
                yield fuss

    def post_init(self):
        """Hook for plugin initialization after the instance was created.

        The name mimics ``__post_init__()`` on dataclasses, without the magic double underscores:
        `Post-init processing <https://docs.python.org/3/library/dataclasses.html#post-init-processing>`_
        """

    def _suggest_when_file_not_found(self):
        suggestion = self.initial_contents
        if not suggestion and self.skip_empty_suggestion:
            return
        logger.info(f"{self}: Suggest initial contents for {self.filename}")

        if suggestion:
            yield self.reporter.make_fuss(SharedViolations.CREATE_FILE_WITH_SUGGESTION, suggestion, fixed=self.autofix)
        else:
            yield self.reporter.make_fuss(SharedViolations.CREATE_FILE)

    def write_file(self, file_exists: bool) -> Optional[Fuss]:  # pylint: disable=unused-argument,no-self-use
        """Hook to write the new file when autofix mode is on. Should be used by inherited classes."""
        return None

    @abc.abstractmethod
    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for this file. It must be overridden by inherited classes if needed."""

    @property
    @abc.abstractmethod
    def initial_contents(self) -> str:
        """Suggested initial content when the file doesn't exist."""

    def write_initial_contents(self, doc_class: Type[BaseDoc], expected_dict: Dict = None) -> str:
        """Helper to write initial contents based on a format."""
        if not expected_dict:
            expected_dict = self.expected_config

        formatted_str = doc_class(obj=expected_dict).reformatted
        if self.autofix:
            self.file_path.parent.mkdir(exist_ok=True, parents=True)
            self.file_path.write_text(formatted_str)
        return formatted_str
