"""JSON files."""
from __future__ import annotations

import json
from itertools import chain
from typing import Iterator

from loguru import logger

from nitpick import fields
from nitpick.blender import BaseDoc, Comparison, JsonDoc, flatten_quotes, unflatten_quotes
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
    Style example: :gitref:`the default config for package.json <src/nitpick/resources/javascript/package-json.toml>`.
    """

    validation_schema = JsonFileSchema
    identify_tags = {"json"}
    violation_base_code = 340
    fixable = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing keys and JSON content."""
        json_doc = JsonDoc(path=self.file_path)
        blender: JsonDict = json_doc.as_object.copy() if self.autofix else {}

        comparison = Comparison(json_doc, self.expected_dict_from_contains_keys(), self.special_config)()
        if comparison.missing:
            yield from self.report(SharedViolations.MISSING_VALUES, blender, comparison.missing)

        comparison = Comparison(json_doc, self.expected_dict_from_contains_json(), self.special_config)()
        if comparison.has_changes:
            yield from chain(
                self.report(SharedViolations.DIFFERENT_VALUES, blender, comparison.diff),
                self.report(SharedViolations.MISSING_VALUES, blender, comparison.missing),
            )

        if self.autofix and self.dirty and blender:
            self.file_path.write_text(JsonDoc(obj=unflatten_quotes(blender)).reformatted)

    def expected_dict_from_contains_keys(self):
        """Expected dict created from "contains_keys" values."""
        return unflatten_quotes(
            {key: VALUE_PLACEHOLDER for key in set(self.expected_config.get(KEY_CONTAINS_KEYS) or [])}
        )

    def expected_dict_from_contains_json(self):
        """Expected dict created from "contains_json" values."""
        expected_config = {}
        # TODO: feat: accept key as a jmespath expression, value is valid JSON
        for key, json_string in (self.expected_config.get(KEY_CONTAINS_JSON) or {}).items():
            try:
                expected_config[key] = json.loads(json_string)
            except json.JSONDecodeError as err:
                # This should not happen, because the style was already validated before.
                # Maybe the NIP??? code was disabled by the user?
                logger.error(f"{err} on {KEY_CONTAINS_JSON} while checking {self.file_path}")
                continue
        return expected_config

    def report(self, violation: ViolationEnum, blender: JsonDict, change: BaseDoc | None):
        """Report a violation while optionally modifying the JSON dict."""
        if not change:
            return
        if blender:
            blender.update(flatten_quotes(change.as_object))
            self.dirty = True
        yield self.reporter.make_fuss(violation, change.reformatted, prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggestion = flatten_quotes(self.expected_dict_from_contains_keys())
        suggestion.update(flatten_quotes(self.expected_dict_from_contains_json()))
        return self.write_initial_contents(JsonDoc, unflatten_quotes(suggestion))


@hookimpl
def plugin_class() -> type[NitpickPlugin]:
    """Handle JSON files."""
    return JsonPlugin


@hookimpl
def can_handle(info: FileInfo) -> type[NitpickPlugin] | None:
    """Handle JSON files."""
    if JsonPlugin.identify_tags & info.tags:
        return JsonPlugin
    return None
