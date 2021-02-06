"""JSON files."""
import json
import logging
from typing import Iterator, Optional, Type

from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.exceptions import NitpickError
from nitpick.formats import JSONFormat
from nitpick.generic import flatten, unflatten
from nitpick.plugins import hookimpl
from nitpick.plugins.base import FilePathTags, NitpickPlugin
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import JsonDict

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"
LOGGER = logging.getLogger(__name__)


class JSONFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains_keys = fields.List(fields.NonEmptyString)
    contains_json = fields.Dict(fields.NonEmptyString, fields.JSONString)


class JsonError(NitpickError):
    """Base for JSON errors."""

    error_base_number = 340


class JSONPlugin(NitpickPlugin):
    """Checker for any JSON file.

    Add the configurations for the file name you wish to check.
    Example: :ref:`the default config for package.json <default-package-json>`.
    """

    error_class = JsonError

    validation_schema = JSONFileSchema
    identify_tags = {"json"}

    SOME_VALUE_PLACEHOLDER = "<some value here>"

    def check_rules(self) -> Iterator[NitpickError]:
        """Check missing keys and JSON content."""
        yield from self._check_contained_keys()
        yield from self._check_contained_json()

    def get_suggested_json(self, raw_actual: JsonDict = None) -> JsonDict:
        """Return the suggested JSON based on actual values."""
        actual = set(flatten(raw_actual).keys()) if raw_actual else set()
        expected = set(self.file_dict.get(KEY_CONTAINS_KEYS) or [])
        # TODO: include "contains_json" keys in the suggestion as well
        missing = expected - actual
        if not missing:
            return {}

        return SortedDict(unflatten({key: self.SOME_VALUE_PLACEHOLDER for key in missing}))

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggestion = self.get_suggested_json()
        return JSONFormat(data=suggestion).reformatted if suggestion else ""

    def _check_contained_keys(self) -> Iterator[NitpickError]:
        json_fmt = JSONFormat(path=self.file_path)
        suggested_json = self.get_suggested_json(json_fmt.as_data)
        if not suggested_json:
            return
        yield self.error_class(" has missing keys:", JSONFormat(data=suggested_json).reformatted, 8)

    def _check_contained_json(self) -> Iterator[NitpickError]:
        actual_fmt = JSONFormat(path=self.file_path)
        expected = {}
        # TODO: accept key as a jmespath expression, value is valid JSON
        for key, json_string in (self.file_dict.get(KEY_CONTAINS_JSON) or {}).items():
            try:
                expected[key] = json.loads(json_string)
            except json.JSONDecodeError as err:
                # This should not happen, because the style was already validated before.
                # Maybe the NIP??? code was disabled by the user?
                LOGGER.error("%s on %s while checking %s", err, KEY_CONTAINS_JSON, self.file_path)
                continue

        yield from self.warn_missing_different(
            JSONFormat(data=actual_fmt.as_data).compare_with_dictdiffer(expected, unflatten)
        )


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return JSONPlugin


@hookimpl
def can_handle(file: FilePathTags) -> Optional["NitpickPlugin"]:
    """Handle JSON files."""
    if JSONPlugin.identify_tags & file.tags:
        return JSONPlugin(file.path_from_root)
    return None
