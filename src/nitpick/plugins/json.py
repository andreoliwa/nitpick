"""JSON files."""
import json
from typing import Dict, Iterator, Optional, Set, Type

from loguru import logger
from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.formats import BaseFormat, JSONFormat
from nitpick.generic import flatten, unflatten
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import JsonDict, MultilineStr
from nitpick.violations import Fuss, ViolationEnum

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"


class JSONFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains_keys = fields.List(fields.NonEmptyString)
    contains_json = fields.Dict(fields.NonEmptyString, fields.JSONString)


class Violations(ViolationEnum):
    """Violations for this plugin."""

    MISSING_KEYS = (348, " has missing keys:")


class JSONPlugin(NitpickPlugin):
    """Enforce configurations for any JSON file.

    Add the configurations for the file name you wish to check.
    Style example: :ref:`the default config for package.json <example-package-json>`.
    """

    validation_schema = JSONFileSchema
    identify_tags = {"json"}
    violation_base_code = 340
    can_fix = True

    SOME_VALUE_PLACEHOLDER = "<some value here>"

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing keys and JSON content."""
        yield from self._check_contained_keys()
        yield from self._check_contained_json()
        # FIXME:
        # json_format = JSONFormat(path=self.file_path)
        # comparison = json_format.compare_with_flatten(self.expected_config)
        # if not comparison.has_changes:
        #     return
        #
        # document = json_format.as_data if self.fix else None
        # if self.fix:
        #     yield from chain(
        #         self.report(SharedViolations.DIFFERENT_VALUES, document, comparison.diff),
        #         self.report(SharedViolations.MISSING_VALUES, document, comparison.missing),
        #     )
        # else:
        #     yield from self._check_contained_keys()
        #     yield from self._check_contained_json()
        #
        # if self.fix and self.dirty:
        #     self.file_path.write_text(JSONFormat(data=document).reformatted)

    def report(self, violation: ViolationEnum, document: Optional[JsonDict], change_dict: Optional[BaseFormat]):
        """Report a violation while optionally modifying the JSON dict."""
        if not change_dict:
            return
        if document:
            document.update(change_dict.as_data)
            self.dirty = True
        yield self.reporter.make_fuss(violation, change_dict.reformatted.strip(), prefix="", fixed=self.fix)

    def get_suggested_json(self, raw_actual: JsonDict = None) -> JsonDict:
        """Return the suggested JSON based on actual values."""
        actual_keys = set(flatten(raw_actual).keys()) if raw_actual else set()
        set_from_contains_keys: Set[str] = set(self.expected_config.get(KEY_CONTAINS_KEYS) or [])
        expected_json_content: Dict[str, MultilineStr] = self.expected_config.get(KEY_CONTAINS_JSON, {})
        expected_keys = set_from_contains_keys | set(expected_json_content.keys())
        missing_keys = expected_keys - actual_keys
        if not missing_keys:
            return {}

        rv = {}
        for key in missing_keys:
            if key in set_from_contains_keys:
                rv[key] = self.SOME_VALUE_PLACEHOLDER
            else:
                # FIXME: this is hacky, only to pass tests; it should go away once I change the commented code above
                # Only suggest JSON content if the file is empty
                if not raw_actual:
                    # FIXME: test invalid json when suggestingfor a new file
                    rv[key] = json.loads(expected_json_content.get(key, ""))
        return SortedDict(unflatten(rv))

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggestion = self.get_suggested_json()
        rv = JSONFormat(data=suggestion).reformatted if suggestion else ""
        if self.fix:
            self.file_path.write_text(rv)
        return rv

    def _check_contained_keys(self) -> Iterator[Fuss]:
        json_fmt = JSONFormat(path=self.file_path)
        suggested_json = self.get_suggested_json(json_fmt.as_data)
        if not suggested_json:
            return
        yield self.reporter.make_fuss(Violations.MISSING_KEYS, JSONFormat(data=suggested_json).reformatted)

    def _check_contained_json(self) -> Iterator[Fuss]:
        actual_fmt = JSONFormat(path=self.file_path)
        expected = {}
        # TODO: accept key as a jmespath expression, value is valid JSON
        for key, json_string in (self.expected_config.get(KEY_CONTAINS_JSON) or {}).items():
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
    """Handle JSON files."""
    return JSONPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle JSON files."""
    if JSONPlugin.identify_tags & info.tags:
        return JSONPlugin
    return None
