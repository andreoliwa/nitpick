"""Style files."""
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from shutil import rmtree
from typing import Dict, Iterator, List, Optional, Set, Tuple, Type
from urllib.parse import urlparse, urlunparse

import click
import requests
from identify import identify
from loguru import logger
from marshmallow import Schema
from pluggy import PluginManager
from slugify import slugify
from toml import TomlDecodeError

from nitpick import __version__, fields
from nitpick.constants import (
    CACHE_DIR_NAME,
    DOT_SLASH,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    PROJECT_NAME,
    PYPROJECT_TOML,
    RAW_GITHUB_CONTENT_BASE_URL,
    TOML_EXTENSION,
)
from nitpick.enums import OptionEnum
from nitpick.exceptions import Deprecation, QuitComplainingError, pretty_exception
from nitpick.formats import TOMLFormat
from nitpick.generic import MergeDict, is_url, search_dict
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.project import Project, climb_directory_tree
from nitpick.schemas import BaseStyleSchema, NitpickSectionSchema, flatten_marshmallow_errors
from nitpick.typedefs import JsonDict, StrOrList, mypy_property
from nitpick.violations import Fuss, Reporter, StyleViolations

Plugins = Set[Type[NitpickPlugin]]


def clear_cache_dir(project_root: Path) -> Path:  # TODO: add unit tests
    """Clear the cache directory (on the project root or on the current directory)."""
    cache_root: Path = project_root / CACHE_DIR_NAME
    project_cache_dir = cache_root / PROJECT_NAME
    rmtree(str(project_cache_dir), ignore_errors=True)
    return project_cache_dir


class Style:
    """Include styles recursively from one another."""

    def __init__(self, project: Project, plugin_manager: PluginManager, offline: bool) -> None:
        self.project: Project = project
        self.plugin_manager: PluginManager = plugin_manager
        self.offline = offline

        self._all_styles = MergeDict()
        self._already_included: Set[str] = set()
        self._first_full_path: str = ""

        self._dynamic_schema_class: type = BaseStyleSchema
        self.rebuild_dynamic_schema()

    @mypy_property
    @lru_cache()
    def cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        return clear_cache_dir(self.project.root)

    @staticmethod
    def get_default_style_url():
        """Return the URL of the default style for the current version."""
        return f"{RAW_GITHUB_CONTENT_BASE_URL}/v{__version__}/{NITPICK_STYLE_TOML}"

    def find_initial_styles(self, configured_styles: StrOrList) -> Iterator[Fuss]:
        """Find the initial style(s) and include them."""
        if configured_styles:
            chosen_styles = configured_styles
            log_message = f"Styles configured in {PYPROJECT_TOML}"
        else:
            paths = climb_directory_tree(self.project.root, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = str(sorted(paths)[0])
                log_message = "Found style climbing the directory tree"
            else:
                chosen_styles = self.get_default_style_url()
                log_message = "Loading default Nitpick style"
        logger.info(log_message + ": {}", chosen_styles)

        yield from self.include_multiple_styles(chosen_styles)

    @staticmethod
    def validate_schema(schema: Type[Schema], path_from_root: str, original_data: JsonDict) -> Dict[str, List[str]]:
        """Validate the schema for the file."""
        if not schema:
            return {}

        inherited_schema = schema is not BaseStyleSchema
        data_to_validate = original_data if inherited_schema else {path_from_root: None}
        local_errors = schema().validate(data_to_validate)
        if local_errors and inherited_schema:
            local_errors = {path_from_root: local_errors}
        return local_errors

    def include_multiple_styles(self, chosen_styles: StrOrList) -> Iterator[Fuss]:
        """Include a list of styles (or just one) into this style tree."""
        style_uris: List[str] = [chosen_styles] if isinstance(chosen_styles, str) else chosen_styles
        for style_uri in style_uris:
            style_path: Optional[Path] = self.get_style_path(style_uri)
            if not style_path:
                continue

            toml = TOMLFormat(path=style_path)
            try:
                read_toml_dict = toml.as_data
            except TomlDecodeError as err:
                # If the TOML itself could not be parsed, we can't go on
                raise QuitComplainingError(
                    Reporter(FileInfo(self.project, style_path.name)).make_fuss(
                        StyleViolations.INVALID_TOML, exception=pretty_exception(err)
                    )
                ) from err

            try:
                display_name = str(style_path.relative_to(self.project.root))
            except ValueError:
                display_name = style_uri

            toml_dict, validation_errors = self._validate_config(read_toml_dict)

            if validation_errors:
                yield Reporter(FileInfo(self.project, display_name)).make_fuss(
                    StyleViolations.INVALID_CONFIG, flatten_marshmallow_errors(validation_errors)
                )

            self._all_styles.add(toml_dict)

            sub_styles = search_dict(NITPICK_STYLES_INCLUDE_JMEX, toml_dict, [])  # type: StrOrList
            if sub_styles:
                yield from self.include_multiple_styles(sub_styles)

    def _validate_config(self, config_dict: Dict) -> Tuple[Dict, Dict]:
        validation_errors = {}
        toml_dict = OrderedDict()
        for key, value_dict in config_dict.items():
            info = FileInfo.create(self.project, key)
            toml_dict[info.path_from_root] = value_dict
            if key == PROJECT_NAME:
                schemas = [NitpickSectionSchema]
            else:
                schemas = [
                    plugin_class.validation_schema
                    for plugin_class in self.plugin_manager.hook.can_handle(info=info)  # pylint: disable=no-member
                ]
                if not schemas:
                    validation_errors[key] = [BaseStyleSchema.error_messages["unknown"]]

            all_errors = {}
            valid_schema = False
            for schema in schemas:
                errors = self.validate_schema(schema, info.path_from_root, value_dict)
                if not errors:
                    # When multiple schemas match a file type, exit when a valid schema is found
                    valid_schema = True
                    break
                all_errors.update(errors)

            if not valid_schema:
                Deprecation.jsonfile_section(all_errors, False)
                validation_errors.update(all_errors)
        return toml_dict, validation_errors

    def get_style_path(self, style_uri: str) -> Optional[Path]:
        """Get the style path from the URI. Add the .toml extension if it's missing."""
        clean_style_uri = style_uri.strip()

        remote = None
        if clean_style_uri.startswith(DOT_SLASH):
            remote = False
        elif is_url(clean_style_uri) or is_url(self._first_full_path):
            remote = True
        elif clean_style_uri:
            remote = False

        if remote is True:
            return self.fetch_style_from_url(clean_style_uri)
        if remote is False:
            return self.fetch_style_from_local_path(clean_style_uri)
        return None

    def fetch_style_from_url(self, url: str) -> Optional[Path]:
        """Fetch a style file from a URL, saving the contents in the cache dir."""
        if self.offline:
            # No style will be fetched in offline mode
            return None

        if self._first_full_path and not is_url(url):
            prefix, rest = self._first_full_path.split(":/")
            domain_plus_url = str(rest).strip("/").rstrip("/") + "/" + url
            new_url = f"{prefix}://{domain_plus_url}"
        else:
            new_url = url

        parsed_url = list(urlparse(new_url))
        if not parsed_url[2].endswith(TOML_EXTENSION):
            parsed_url[2] += TOML_EXTENSION
        new_url = urlunparse(parsed_url)

        if new_url in self._already_included:
            return None

        if not self.cache_dir:
            raise FileNotFoundError("Cache dir does not exist")

        try:
            response = requests.get(new_url)
        except requests.ConnectionError:
            click.secho(
                "Your network is unreachable. Fix your connection or use"
                f" {OptionEnum.OFFLINE.as_flake8_flag()} / {OptionEnum.OFFLINE.as_envvar()}=1",
                fg="red",
                err=True,
            )
            return None
        if not response.ok:
            raise FileNotFoundError(f"Error {response} fetching style URL {new_url}")

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = new_url.rsplit("/", 1)[0]

        contents = response.text
        style_path = self.cache_dir / f"{slugify(new_url)}.toml"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        style_path.write_text(contents)

        logger.debug("Loading style from URL {} into {}", new_url, style_path)
        self._already_included.add(new_url)

        return style_path

    def fetch_style_from_local_path(self, partial_filename: str) -> Optional[Path]:
        """Fetch a style file from a local path."""
        if partial_filename and not partial_filename.endswith(TOML_EXTENSION):
            partial_filename += TOML_EXTENSION
        expanded_path = Path(partial_filename).expanduser()

        if self._first_full_path and not (str(expanded_path).startswith("/") or partial_filename.startswith(DOT_SLASH)):
            # Prepend the previous path to the partial file name.
            style_path = Path(self._first_full_path) / expanded_path
        else:
            # Get the absolute path, be it from a root path (starting with slash) or from the current dir.
            style_path = Path(expanded_path).absolute()

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = str(style_path.resolve().parent)

        if str(style_path) in self._already_included:
            return None

        if not style_path.exists():
            raise FileNotFoundError(f"Local style file does not exist: {style_path}")

        logger.debug(f"Loading style from {style_path}")
        self._already_included.add(str(style_path))
        return style_path

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        if not self.cache_dir:
            return {}
        merged_dict = self._all_styles.merge()
        # TODO: check if the merged style file is still needed
        merged_style_path = self.cache_dir / MERGED_STYLE_TOML  # type: Path
        toml = TOMLFormat(data=merged_dict)

        attempt = 1
        while attempt < 5:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                merged_style_path.write_text(toml.reformatted)
                break
            except OSError:
                attempt += 1

        return merged_dict

    @staticmethod
    def file_field_pair(filename: str, base_file_class: Type[NitpickPlugin]) -> Dict[str, fields.Field]:
        """Return a schema field with info from a config file class."""
        unique_filename_with_underscore = slugify(filename, separator="_")

        kwargs = {"data_key": filename}
        if base_file_class.validation_schema:
            field = fields.Nested(base_file_class.validation_schema, **kwargs)
        else:
            # For default files (pyproject.toml, setup.cfg...), there is no strict schema;
            # it can be anything they allow.
            # It's out of Nitpick's scope to validate those files.
            field = fields.Dict(fields.String, **kwargs)
        return {unique_filename_with_underscore: field}

    @lru_cache()
    def load_fixed_dynamic_classes(self) -> Tuple[Plugins, Plugins]:
        """Separate classes with fixed file names from classes with dynamic files names."""
        fixed_name_classes: Plugins = set()
        dynamic_name_classes: Plugins = set()
        for plugin_class in self.plugin_manager.hook.plugin_class():  # pylint: disable=no-member
            if plugin_class.filename:
                fixed_name_classes.add(plugin_class)
            else:
                dynamic_name_classes.add(plugin_class)
        return fixed_name_classes, dynamic_name_classes

    def rebuild_dynamic_schema(self, data: JsonDict = None) -> None:
        """Rebuild the dynamic Marshmallow schema when needed, adding new fields that were found on the style."""
        new_files_found: Dict[str, fields.Field] = OrderedDict()

        fixed_name_classes, dynamic_name_classes = self.load_fixed_dynamic_classes()

        if data is None:
            # Data is empty; so this is the first time the dynamic class is being rebuilt.
            # Loop on classes with predetermined names, and add fields for them on the dynamic validation schema.
            # E.g.: setup.cfg, pre-commit, pyproject.toml: files whose names we already know at this point.
            for subclass in fixed_name_classes:
                new_files_found.update(self.file_field_pair(subclass.filename, subclass))
        else:
            handled_tags: Dict[str, Type[NitpickPlugin]] = {}

            # Data was provided; search it to find new dynamic files to add to the validation schema).
            # E.g.: JSON files that were configured on some TOML style file.
            for subclass in dynamic_name_classes:
                for tag in subclass.identify_tags:
                    # TODO: WRONG! a tag should be handled by multiple classes...
                    # A tag can only be handled by a single subclass.
                    # If more than one class handle a tag, the latest one will be the handler.
                    handled_tags[tag] = subclass

                jmex = subclass.get_compiled_jmespath_filenames()
                for configured_filename in search_dict(jmex, data, []):
                    new_files_found.update(self.file_field_pair(configured_filename, subclass))

            self._find_subclasses(data, handled_tags, new_files_found)

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
