"""JSON files."""
import json
from typing import Iterator, Optional, Type

from loguru import logger
from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.exceptions import CodeEnum, NitpickError
from nitpick.formats import JSONFormat
from nitpick.generic import flatten, unflatten
from nitpick.plugins import hookimpl
from nitpick.plugins.base import FileData, NitpickPlugin
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import JsonDict

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"


class JSONFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains_keys = fields.List(fields.NonEmptyString)
    contains_json = fields.Dict(fields.NonEmptyString, fields.JSONString)


class JSONPlugin(NitpickPlugin):
    """Enforce configurations for any JSON file.

    Add the configurations for the file name you wish to check.
    Example: :ref:`the default config for package.json <default-package-json>`.
    """

    validation_schema = JSONFileSchema
    identify_tags = {"json"}
    error_base_code = 340
    # FIXME[AA]: reporter = Reporter(340, JsonCodes: CodeEnum)
    #  self.reporter.make_error(...)

    SOME_VALUE_PLACEHOLDER = "<some value here>"

    class Codes(CodeEnum):
        """Error codes for this plugin."""

        MissingKeys = (348, " has missing keys:")

    def enforce_rules(self) -> Iterator[NitpickError]:
        """Enforce rules for missing keys and JSON content."""
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
        yield self.make_error(self.Codes.MissingKeys, JSONFormat(data=suggested_json).reformatted)

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
                logger.error(f"{err} on {KEY_CONTAINS_JSON} while checking {self.file_path}")
                continue

        yield from self.warn_missing_different(
            JSONFormat(data=actual_fmt.as_data).compare_with_dictdiffer(expected, unflatten)
        )


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return JSONPlugin


@hookimpl
def can_handle(data: FileData) -> Optional["NitpickPlugin"]:
    """Handle JSON files."""
    if JSONPlugin.identify_tags & data.tags:
        return JSONPlugin(data)
    return None
