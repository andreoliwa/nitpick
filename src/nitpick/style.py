"""Style files."""
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Set, Type
from urllib.parse import urlparse, urlunparse

import requests
from slugify import slugify
from toml import TomlDecodeError

from nitpick import Nitpick, __version__, fields
from nitpick.constants import (
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    RAW_GITHUB_CONTENT_BASE_URL,
    TOML_EXTENSION,
)
from nitpick.files.base import BaseFile
from nitpick.files.pyproject_toml import PyProjectTomlFile
from nitpick.formats import TomlFormat
from nitpick.generic import MergeDict, climb_directory_tree, is_url, pretty_exception, search_dict
from nitpick.schemas import BaseStyleSchema, flatten_marshmallow_errors
from nitpick.typedefs import JsonDict, StrOrList

LOGGER = logging.getLogger(__name__)


class Style:
    """Include styles recursively from one another."""

    def __init__(self) -> None:
        self._all_styles = MergeDict()
        self._already_included = set()  # type: Set[str]
        self._first_full_path = ""  # type: str

        self._dynamic_schema_class = BaseStyleSchema  # type: type
        self.rebuild_dynamic_schema()

    @staticmethod
    def get_default_style_url():
        """Return the URL of the default style for the current version."""
        return "{}/v{}/{}".format(RAW_GITHUB_CONTENT_BASE_URL, __version__, NITPICK_STYLE_TOML)

    def find_initial_styles(self, configured_styles: StrOrList):
        """Find the initial style(s) and include them."""
        if configured_styles:
            chosen_styles = configured_styles
            log_message = "Styles configured in {}: %s".format(PyProjectTomlFile.file_name)
        else:
            paths = climb_directory_tree(Nitpick.current_app().root_dir, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = str(sorted(paths)[0])
                log_message = "Found style climbing the directory tree: %s"
            else:
                chosen_styles = self.get_default_style_url()
                log_message = "Loading default Nitpick style %s"
        LOGGER.info(log_message, chosen_styles)

        self.include_multiple_styles(chosen_styles)

    def validate_style(self, style_file_name: str, original_data: JsonDict):
        """Validate a style file (TOML) against a Marshmallow schema."""
        self.rebuild_dynamic_schema(original_data)
        style_errors = self._dynamic_schema_class().validate(original_data)
        if style_errors:
            Nitpick.current_app().add_style_error(
                style_file_name, "Invalid config:", flatten_marshmallow_errors(style_errors)
            )

    def include_multiple_styles(self, chosen_styles: StrOrList) -> None:
        """Include a list of styles (or just one) into this style tree."""
        style_uris = [chosen_styles] if isinstance(chosen_styles, str) else chosen_styles  # type: List[str]
        for style_uri in style_uris:
            style_path = self.get_style_path(style_uri)  # type: Optional[Path]
            if not style_path:
                continue

            toml = TomlFormat(path=style_path)
            try:
                toml_dict = toml.as_data
            except TomlDecodeError as err:
                Nitpick.current_app().add_style_error(style_path.name, pretty_exception(err, "Invalid TOML"))
                # If the TOML itself could not be parsed, we can't go on
                return

            try:
                display_name = str(style_path.relative_to(Nitpick.current_app().root_dir))
            except ValueError:
                display_name = style_uri
            self.validate_style(display_name, toml_dict)
            self._all_styles.add(toml_dict)

            sub_styles = search_dict(NITPICK_STYLES_INCLUDE_JMEX, toml_dict, [])  # type: StrOrList
            if sub_styles:
                self.include_multiple_styles(sub_styles)

    def get_style_path(self, style_uri: str) -> Optional[Path]:
        """Get the style path from the URI. Add the .toml extension if it's missing."""
        clean_style_uri = style_uri.strip()

        style_path = None
        if is_url(clean_style_uri) or is_url(self._first_full_path):
            style_path = self.fetch_style_from_url(clean_style_uri)
        elif clean_style_uri:
            style_path = self.fetch_style_from_local_path(clean_style_uri)
        return style_path

    def fetch_style_from_url(self, url: str) -> Optional[Path]:
        """Fetch a style file from a URL, saving the contents in the cache dir."""
        if self._first_full_path and not is_url(url):
            prefix, rest = self._first_full_path.split(":/")
            domain_plus_url = str(rest).strip("/").rstrip("/") + "/" + url
            new_url = "{}://{}".format(prefix, domain_plus_url)
        else:
            new_url = url

        parsed_url = list(urlparse(new_url))
        if not parsed_url[2].endswith(TOML_EXTENSION):
            parsed_url[2] += TOML_EXTENSION
        new_url = urlunparse(parsed_url)

        if new_url in self._already_included:
            return None

        if not Nitpick.current_app().cache_dir:
            raise FileNotFoundError("Cache dir does not exist")

        response = requests.get(new_url)
        if not response.ok:
            raise FileNotFoundError("Error {} fetching style URL {}".format(response, new_url))

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = new_url.rsplit("/", 1)[0]

        contents = response.text
        style_path = Nitpick.current_app().cache_dir / "{}.toml".format(slugify(new_url))
        Nitpick.current_app().cache_dir.mkdir(parents=True, exist_ok=True)
        style_path.write_text(contents)

        LOGGER.info("Loading style from URL %s into %s", new_url, style_path)
        self._already_included.add(new_url)

        return style_path

    def fetch_style_from_local_path(self, partial_file_name: str) -> Optional[Path]:
        """Fetch a style file from a local path."""
        if partial_file_name and not partial_file_name.endswith(TOML_EXTENSION):
            partial_file_name += TOML_EXTENSION
        expanded_path = Path(partial_file_name).expanduser()

        if not str(expanded_path).startswith("/") and self._first_full_path:
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
            raise FileNotFoundError("Local style file does not exist: {}".format(style_path))

        LOGGER.info("Loading style from file: %s", style_path)
        self._already_included.add(str(style_path))
        return style_path

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        if not Nitpick.current_app().cache_dir:
            return {}
        merged_dict = self._all_styles.merge()
        merged_style_path = Nitpick.current_app().cache_dir / MERGED_STYLE_TOML  # type: Path
        toml = TomlFormat(data=merged_dict)

        attempt = 1
        while attempt < 5:
            try:
                Nitpick.current_app().cache_dir.mkdir(parents=True, exist_ok=True)
                merged_style_path.write_text(toml.reformatted)
                break
            except OSError:
                attempt += 1

        return merged_dict

    @staticmethod
    def file_field_pair(file_name: str, base_file_class: Type[BaseFile]) -> Dict[str, fields.Field]:
        """Return a schema field with info from a config file class."""
        valid_toml_key = TomlFormat.group_name_for(file_name)
        unique_file_name_with_underscore = slugify(file_name, separator="_")

        kwargs = {"data_key": valid_toml_key}
        if base_file_class.nested_field:
            field = fields.Nested(base_file_class.nested_field, **kwargs)
        else:
            # For default files (pyproject.toml, setup.cfg...), there is no strict schema;
            # it can be anything they allow.
            # It's out of Nitpick's scope to validate those files.
            field = fields.Dict(fields.String, **kwargs)
        return {unique_file_name_with_underscore: field}

    def rebuild_dynamic_schema(self, data: JsonDict = None) -> None:
        """Rebuild the dynamic Marshmallow schema when needed, adding new fields that were found on the style."""
        new_files_found = OrderedDict()  # type: Dict[str, fields.Field]

        if data is None:
            # Data is empty; so this is the first time the dynamic class is being rebuilt.
            # Loop on classes with predetermined names, and add fields for them on the dynamic validation schema.
            # E.g.: setup.cfg, pre-commit, pyproject.toml: files whose names we already know at this point.
            for subclass in BaseFile.fixed_name_classes:
                new_files_found.update(self.file_field_pair(subclass.file_name, subclass))
        else:
            # Data was provided; search it to find new dynamic files to add to the validation schema).
            # E.g.: JSON files that were configured on some TOML style file.
            for subclass in BaseFile.dynamic_name_classes:
                jmex = subclass.get_compiled_jmespath_file_names()
                for configured_file_name in search_dict(jmex, data, []):
                    new_files_found.update(self.file_field_pair(configured_file_name, subclass))

        # Only recreate the schema if new fields were found.
        if new_files_found:
            self._dynamic_schema_class = type("DynamicStyleSchema", (self._dynamic_schema_class,), new_files_found)
