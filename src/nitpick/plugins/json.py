"""JSON files."""
import json
import logging
from typing import Optional, Set, Type

from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.formats import JSONFormat
from nitpick.generic import flatten, unflatten
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import JsonDict, YieldFlake8Error

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"
LOGGER = logging.getLogger(__name__)


class JSONFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains_keys = fields.List(fields.NonEmptyString)
    contains_json = fields.Dict(fields.NonEmptyString, fields.JSONString)


class JSONPlugin(NitpickPlugin):
    """Checker for any JSON file.

    Add the configurations for the file name you wish to check.
    Example: :ref:`the default config for package.json <default-package-json>`.
    """

    error_base_number = 340

    validation_schema = JSONFileSchema
    identify_tags = {"json"}

    SOME_VALUE_PLACEHOLDER = "<some value here>"

    def check_rules(self) -> YieldFlake8Error:
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

    def _check_contained_keys(self) -> YieldFlake8Error:
        json_fmt = JSONFormat(path=self.file_path)
        suggested_json = self.get_suggested_json(json_fmt.as_data)
        if not suggested_json:
            return
        yield self.flake8_error(8, " has missing keys:", JSONFormat(data=suggested_json).reformatted)

    def _check_contained_json(self) -> YieldFlake8Error:
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
def handle_config_file(config: JsonDict, file_name: str, tags: Set[str]) -> Optional["NitpickPlugin"]:
    """Handle JSON files."""
    return JSONPlugin(config, file_name) if "json" in tags else None
