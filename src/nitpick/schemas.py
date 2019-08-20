"""Marshmallow schemas."""
from typing import Dict

from marshmallow import Schema, ValidationError, fields
from marshmallow_polyfield import PolyField
from sortedcontainers import SortedDict

from nitpick.files.setup_cfg import SetupCfgFile
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


def validate_section_dot_field(section_field: str) -> bool:
    """Validate if the combinatio section/field has a dot separating them."""
    # FIXME: add tests for these situations
    common = "Use this format: section_name.field_name"
    if "." not in section_field:
        raise ValidationError("Dot is missing. {}".format(common))
    parts = section_field.split(".")
    if len(parts) > 2:
        raise ValidationError("There's more than one dot. {}".format(common))
    if not parts[0].strip():
        raise ValidationError("Empty section name. {}".format(common))
    if not parts[1].strip():
        raise ValidationError("Empty field name. {}".format(common))
    return True


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


class SetupCfgSchema(Schema):
    """Validation schema for setup.cfg."""

    comma_separated_values = fields.List(fields.String(validate=validate_section_dot_field))


class NitpickFilesSchema(Schema):
    """Validation schema for the ``[nitpick.files]`` section on the style file."""

    absent = fields.Dict(NotEmptyString(), fields.String())
    present = fields.Dict(NotEmptyString(), fields.String())
    # TODO: load this schema dynamically, then add this next field setup_cfg
    setup_cfg = fields.Nested(SetupCfgSchema, data_key=SetupCfgFile.file_name)


class NitpickSchema(Schema):
    """Validation schema for the ``[nitpick]`` section on the style file."""

    minimum_version = NotEmptyString()
    styles = fields.Nested(NitpickStylesSchema)
    files = fields.Nested(NitpickFilesSchema)
    # TODO: load this schema dynamically, then add this next field JsonFile
    JsonFile = fields.Nested(NitpickJsonFileSchema)


class BaseStyleSchema(Schema):
    """Base validation schema for style files. Dynamic fields will be added to it later."""

    nitpick = fields.Nested(NitpickSchema)
