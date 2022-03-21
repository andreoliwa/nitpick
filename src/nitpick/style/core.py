"""Style files."""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence, Set, Type

import dpath.util
from flatten_dict import flatten, unflatten
from furl import furl
from identify import identify
from loguru import logger
from more_itertools import always_iterable
from slugify import slugify
from toml import TomlDecodeError

from nitpick import __version__, fields
from nitpick.blender import SEPARATOR_FLATTEN, TomlDoc, custom_reducer, custom_splitter, search_json
from nitpick.constants import (
    CACHE_DIR_NAME,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    PROJECT_NAME,
    PROJECT_OWNER,
    PYPROJECT_TOML,
)
from nitpick.exceptions import QuitComplainingError, pretty_exception
from nitpick.generic import furl_path_to_python_path
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.project import Project, glob_files
from nitpick.schemas import BaseStyleSchema, flatten_marshmallow_errors
from nitpick.style.config import ConfigValidator
from nitpick.style.fetchers import Scheme, StyleFetcherManager
from nitpick.style.fetchers.github import GitHubURL
from nitpick.typedefs import JsonDict
from nitpick.violations import Fuss, Reporter, StyleViolations

Plugins = Set[Type[NitpickPlugin]]


@dataclass()
class StyleManager:  # pylint: disable=too-many-instance-attributes
    """Include styles recursively from one another."""

    project: Project
    offline: bool
    cache_option: str

    _cache_dir: Path = field(init=False)
    _fixed_name_classes: set = field(init=False)

    def __post_init__(self) -> None:
        """Initialize dependant fields."""
        self._merged_styles: JsonDict = {}
        self._already_included: set[str] = set()
        self._dynamic_schema_class: type = BaseStyleSchema
        self._style_fetcher_manager = StyleFetcherManager(self.offline, self.cache_dir, self.cache_option)
        self._config_validator = ConfigValidator(self.project)
        self.rebuild_dynamic_schema()

    def __hash__(self):
        """Calculate hash on hashable items so lru_cache knows how to cache data from this class."""
        return hash((self.project, self.offline, self.cache_option))

    @property
    def cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        try:
            path = self._cache_dir
        except AttributeError:
            self._cache_dir = path = self.project.root / CACHE_DIR_NAME / PROJECT_NAME
            # TODO: fix: check if the merged style file is still needed
            #  if not, this line can be removed
            path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_default_style_url(github=False) -> furl:
        """Return the URL of the default style/preset."""
        if github:
            return GitHubURL(PROJECT_OWNER, PROJECT_NAME, f"v{__version__}", (NITPICK_STYLE_TOML,)).long_protocol_url

        return furl(scheme=Scheme.PY, host=PROJECT_NAME, path=["resources", "presets", PROJECT_NAME])

    def find_initial_styles(self, configured_styles: Sequence[str], base: str | None = None) -> Iterator[Fuss]:
        """Find the initial style(s) and include them.

        base is the URL for the source of the initial styles, and is used to
        resolve relative references. If omitted, defaults to the project root.

        """
        project_root = self.project.root

        if configured_styles:
            chosen_styles = configured_styles
            logger.info(f"Using styles configured in {PYPROJECT_TOML}: {chosen_styles}")
        else:
            paths = glob_files(project_root, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = [sorted(paths)[0].expanduser().resolve().as_uri()]
                log_message = "Using local style found climbing the directory tree"
            else:
                chosen_styles = [self.get_default_style_url()]
                log_message = "Using default remote Nitpick style"
            logger.info(f"{log_message}: {chosen_styles[0]}")

        base_url = furl(base or project_root.resolve().as_uri())
        yield from self.include_multiple_styles(
            self._style_fetcher_manager.normalize_url(ref, base_url) for ref in chosen_styles
        )

    def include_multiple_styles(self, chosen_styles: Iterable[furl]) -> Iterator[Fuss]:
        """Include a list of styles (or just one) into this style tree."""
        for style_url in chosen_styles:
            yield from self._include_style(style_url)

    def _include_style(self, style_url: furl) -> Iterator[Fuss]:
        if style_url.url in self._already_included:
            return
        self._already_included.add(style_url.url)

        file_contents = self._style_fetcher_manager.fetch(style_url)
        if file_contents is None:
            return

        # generate a 'human readable' version of the URL; a relative path for local files
        # and the URL otherwise.
        display_name = style_url.url
        if style_url.scheme == "file":
            path = furl_path_to_python_path(style_url.path)
            with suppress(ValueError):
                path = path.relative_to(self.project.root)
            display_name = str(path)

        read_toml_dict = self._read_toml(file_contents, display_name)

        # normalize sub-style URIs, before merging
        sub_styles = [
            self._style_fetcher_manager.normalize_url(ref, style_url)
            for ref in always_iterable(search_json(read_toml_dict, NITPICK_STYLES_INCLUDE_JMEX, []))
        ]
        if sub_styles:
            read_toml_dict.setdefault("nitpick", {}).setdefault("styles", {})["include"] = [
                str(url) for url in sub_styles
            ]

        toml_dict, validation_errors = self._config_validator.validate(read_toml_dict)

        if validation_errors:
            yield Reporter(FileInfo(self.project, display_name)).make_fuss(
                StyleViolations.INVALID_CONFIG, flatten_marshmallow_errors(validation_errors)
            )

        dpath.util.merge(self._merged_styles, flatten(toml_dict, custom_reducer(SEPARATOR_FLATTEN)))

        yield from self.include_multiple_styles(sub_styles)

    def _read_toml(self, file_contents: str, display_name: str) -> JsonDict:
        toml = TomlDoc(string=file_contents)
        try:
            read_toml_dict = toml.as_object
        # TODO: refactor: replace by this error when using tomlkit only in the future:
        #  except TOMLKitError as err:
        except TomlDecodeError as err:
            # If the TOML itself could not be parsed, we can't go on
            raise QuitComplainingError(
                Reporter(FileInfo(self.project, display_name)).make_fuss(
                    StyleViolations.INVALID_TOML, exception=pretty_exception(err)
                )
            ) from err
        return read_toml_dict

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        merged_dict = unflatten(self._merged_styles, custom_splitter(SEPARATOR_FLATTEN))
        # TODO: fix: check if the merged style file is still needed
        merged_style_path: Path = self.cache_dir / MERGED_STYLE_TOML
        toml = TomlDoc(obj=merged_dict)

        attempt = 1
        while attempt < 5:
            try:
                merged_style_path.write_text(toml.reformatted)
                break
            except OSError:
                attempt += 1

        return merged_dict

    @staticmethod
    def file_field_pair(filename: str, base_file_class: type[NitpickPlugin]) -> dict[str, fields.Field]:
        """Return a schema field with info from a config file class."""
        unique_filename_with_underscore = slugify(filename, separator="_")

        kwargs = {"data_key": filename}
        if base_file_class.validation_schema:
            file_field = fields.Nested(base_file_class.validation_schema, **kwargs)
        else:
            # For some files (e.g.: TOML/ INI files), there is no strict schema;
            # it can be anything they allow.
            # It's out of Nitpick's scope to validate those files.
            file_field = fields.Dict(fields.String, **kwargs)
        return {unique_filename_with_underscore: file_field}

    def load_fixed_name_plugins(self) -> Plugins:
        """Separate classes with fixed file names from classes with dynamic files names."""
        try:
            fixed_name_classes = self._fixed_name_classes
        except AttributeError:
            fixed_name_classes = self._fixed_name_classes = {
                plugin_class
                for plugin_class in self.project.plugin_manager.hook.plugin_class()  # pylint: disable=no-member
                if plugin_class.filename
            }
        return fixed_name_classes

    def rebuild_dynamic_schema(self) -> None:
        """Rebuild the dynamic Marshmallow schema when needed, adding new fields that were found on the style."""
        new_files_found: dict[str, fields.Field] = {}

        fixed_name_classes = self.load_fixed_name_plugins()

        for subclass in fixed_name_classes:
            new_files_found.update(self.file_field_pair(subclass.filename, subclass))

        # Only recreate the schema if new fields were found.
        if new_files_found:
            self._dynamic_schema_class = type("DynamicStyleSchema", (self._dynamic_schema_class,), new_files_found)

    def _find_subclasses(self, data, handled_tags, new_files_found):
        for possible_file in data.keys():
            found_subclasses = []
            for file_tag in identify.tags_from_filename(possible_file):
                handler_subclass = handled_tags.get(file_tag)
                if handler_subclass:
                    found_subclasses.append(handler_subclass)

            for found_subclass in found_subclasses:
                new_files_found.update(self.file_field_pair(possible_file, found_subclass))
