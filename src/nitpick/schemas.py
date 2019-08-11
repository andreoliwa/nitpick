"""Marshmallow schemas."""
from typing import Dict

from marshmallow import Schema, fields
from marshmallow_polyfield import PolyField
from sortedcontainers import SortedDict

from nitpick.generic import flatten
from nitpick.validators import TrimmedLength


class NotEmptyString(fields.String):
    """A string field that must not be empty even after trimmed."""

    def __init__(self, **kwargs):
        super().__init__(validate=TrimmedLength(min=1), **kwargs)


def flatten_marshmallow_errors(errors: Dict) -> str:
    """Flatten Marshmallow errors to a string."""
    formatted = []
    for field, data in SortedDict(flatten(errors)).items():
        if isinstance(data, list):
            messages_per_field = ["{}: {}".format(field, ", ".join(data))]
        elif isinstance(data, dict):
            messages_per_field = [
                "{}[{}]: {}".format(field, index, ", ".join(messages)) for index, messages in data.items()
            ]
        else:
            # This should never happen; if it does, let's just convert to a string
            messages_per_field = [str(errors)]
        formatted.append("\n".join(messages_per_field))
    return "\n".join(formatted)


def string_or_list_field(object_dict, parent_object_dict):  # pylint: disable=unused-argument
    """Detect if the field is a string or a list."""
    if isinstance(object_dict, list):
        return fields.List(NotEmptyString(required=True, allow_none=False))
    return NotEmptyString()


def boolean_or_dict_field(object_dict, parent_object_dict):  # pylint: disable=unused-argument
    """Detect if the field is a boolean or a dict."""
    if isinstance(object_dict, dict):
        return fields.Dict
    return fields.Bool


class ToolNitpickSchema(Schema):
    """Validation schema for the ``[tool.nitpick]`` section on ``pyproject.toml``."""

    style = PolyField(deserialization_schema_selector=string_or_list_field)


class NitpickStylesSchema(Schema):
    """Validation schema for the ``[nitpick.styles]`` section on the style file."""

    include = PolyField(deserialization_schema_selector=string_or_list_field)


class NitpickJsonFileSchema(Schema):
    """Validation schema for the ``[nitpick.JsonFile]`` section on the style file."""

    file_names = fields.List(fields.String)


class NitpickSchema(Schema):
    """Validation schema for the ``[nitpick]`` section on the style file."""

    minimum_version = NotEmptyString()
    styles = fields.Nested(NitpickStylesSchema)
    files = fields.Dict(fields.String, PolyField(deserialization_schema_selector=boolean_or_dict_field))
    JsonFile = fields.Nested(NitpickJsonFileSchema)


class MergedStyleSchema(Schema):
    """Validation schema for the merged style file."""

    nitpick = fields.Nested(NitpickSchema)
