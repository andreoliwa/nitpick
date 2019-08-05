"""Checker for JSON files."""
import json

from sortedcontainers import SortedDict

from nitpick.files.base import BaseFile
from nitpick.formats import JsonFormat
from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, YieldFlake8Error

KEY_CONTAINS_KEYS = "contains_keys"
KEY_CONTAINS_JSON = "contains_json"


class JsonFile(BaseFile):
    """Checker for JSON files."""

    has_multiple_files = True
    error_base_number = 340

    SOME_VALUE_PLACEHOLDER = "<some value here>"

    def check_rules(self) -> YieldFlake8Error:
        """Check missing keys and JSON content."""
        for _ in self.multiple_files:
            yield from self._check_contained_keys()
            yield from self._check_contained_json()

    def get_suggested_json(self, raw_actual: JsonDict = None) -> JsonDict:
        """Return the suggested JSON based on actual values."""
        actual = set(flatten(raw_actual).keys()) if raw_actual else set()
        expected = set(self.file_dict.get(KEY_CONTAINS_KEYS) or [])
        missing = expected - actual
        if not missing:
            return {}

        return SortedDict(unflatten({key: self.SOME_VALUE_PLACEHOLDER for key in missing}))

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggestion = self.get_suggested_json()
        return JsonFormat(data=suggestion).reformatted if suggestion else ""

    def _check_contained_keys(self) -> YieldFlake8Error:
        json_fmt = JsonFormat(path=self.file_path)
        suggested_json = self.get_suggested_json(json_fmt.as_data)
        if not suggested_json:
            return
        yield self.flake8_error(8, " has missing keys:", JsonFormat(data=suggested_json).reformatted)

    def _check_contained_json(self) -> YieldFlake8Error:
        actual_fmt = JsonFormat(path=self.file_path)
        expected = {
            # FIXME: deal with invalid JSON
            # TODO: accept key as a jmespath expression, value is valid JSON
            key: json.loads(json_string)
            for key, json_string in (self.file_dict.get(KEY_CONTAINS_JSON) or {}).items()
        }
        yield from self.warn_missing_different(JsonFormat(data=actual_fmt.as_data).compare_with_dictdiffer(expected))
