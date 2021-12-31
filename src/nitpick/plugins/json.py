"""JSON files."""
import json
from itertools import chain
from typing import Iterator, Optional, Type

from loguru import logger

from nitpick import fields
from nitpick.documents import BaseDoc, JsonDoc
from nitpick.generic import DictBlender, flatten, unflatten
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import JsonDict
from nitpick.violations import Fuss, SharedViolations, ViolationEnum

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"
VALUE_PLACEHOLDER = "<some value here>"


class JsonFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains_keys = fields.List(fields.NonEmptyString)
    contains_json = fields.Dict(fields.NonEmptyString, fields.JsonString)


class JsonPlugin(NitpickPlugin):
    """Enforce configurations and autofix JSON files.

    Add the configurations for the file name you wish to check.
    Style example: :ref:`the default config for package.json <example-package-json>`.
    """

    validation_schema = JsonFileSchema
    identify_tags = {"json"}
    violation_base_code = 340
    fixable = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing keys and JSON content."""
        actual = JsonDoc(path=self.file_path)
        final_dict: Optional[JsonDict] = flatten(actual.as_object) if self.autofix else None

        comparison = actual.compare_with_flatten(self.expected_dict_from_contains_keys())
        if comparison.missing:
            yield from self.report(SharedViolations.MISSING_VALUES, final_dict, comparison.missing)

        comparison = actual.compare_with_flatten(self.expected_dict_from_contains_json())
        if comparison.has_changes:
            yield from chain(
                self.report(SharedViolations.DIFFERENT_VALUES, final_dict, comparison.diff),
                self.report(SharedViolations.MISSING_VALUES, final_dict, comparison.missing),
            )

        if self.autofix and self.dirty and final_dict:
            self.file_path.write_text(JsonDoc(obj=unflatten(final_dict)).reformatted)

    def expected_dict_from_contains_keys(self):
        """Expected dict created from "contains_keys" values."""
        return unflatten({key: VALUE_PLACEHOLDER for key in set(self.expected_config.get(KEY_CONTAINS_KEYS) or [])})

    def expected_dict_from_contains_json(self):
        """Expected dict created from "contains_json" values."""
        expected_config = {}
        # TODO: accept key as a jmespath expression, value is valid JSON
        for key, json_string in (self.expected_config.get(KEY_CONTAINS_JSON) or {}).items():
            try:
                expected_config[key] = json.loads(json_string)
            except json.JSONDecodeError as err:
                # This should not happen, because the style was already validated before.
                # Maybe the NIP??? code was disabled by the user?
                logger.error(f"{err} on {KEY_CONTAINS_JSON} while checking {self.file_path}")
                continue
        return expected_config

    def report(self, violation: ViolationEnum, final_dict: Optional[JsonDict], change: Optional[BaseDoc]):
        """Report a violation while optionally modifying the JSON dict."""
        if not change:
            return
        if final_dict:
            final_dict.update(flatten(change.as_object))
            self.dirty = True
        yield self.reporter.make_fuss(violation, change.reformatted, prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggestion = DictBlender(self.expected_dict_from_contains_keys())
        suggestion.add(self.expected_dict_from_contains_json())
        return self.write_initial_contents(JsonDoc, suggestion.mix())


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """Handle JSON files."""
    return JsonPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle JSON files."""
    if JsonPlugin.identify_tags & info.tags:
        return JsonPlugin
    return None
