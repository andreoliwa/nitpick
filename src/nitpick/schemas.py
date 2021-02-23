"""Marshmallow schemas."""
from typing import Dict

from marshmallow import Schema
from marshmallow_polyfield import PolyField
from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.constants import READ_THE_DOCS_URL
from nitpick.generic import flatten


def flatten_marshmallow_errors(errors: Dict) -> str:
    """Flatten Marshmallow errors to a string."""
    formatted = []
    for field, data in SortedDict(flatten(errors)).items():
        if isinstance(data, list):
            messages_per_field = [f"{field}: {', '.join(data)}"]
        elif isinstance(data, dict):
            messages_per_field = [f"{field}[{index}]: {', '.join(messages)}" for index, messages in data.items()]
        else:
            # This should never happen; if it does, let's just convert to a string
            messages_per_field = [str(errors)]
        formatted.append("\n".join(messages_per_field))
    return "\n".join(formatted)


def help_message(sentence: str, help_page: str) -> str:
    """Show help with the documentation URL on validation errors."""
    clean_sentence = sentence.strip(" .")
    return f"{clean_sentence}. See {READ_THE_DOCS_URL}{help_page}."


class BaseNitpickSchema(Schema):
    """Base schema for all others, with default error messages."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html")}


class NitpickStylesSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick.styles]`` section on the style file."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html#nitpick-styles")}

    include = PolyField(deserialization_schema_selector=fields.string_or_list_field)


class SetupCfgSchema(BaseNitpickSchema):
    """Validation schema for setup.cfg."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html#comma-separated-values")}

    comma_separated_values = fields.List(fields.String(validate=fields.validate_section_dot_field))


class NitpickFilesSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick.files]`` section on the style file."""

    error_messages = {"unknown": help_message("Unknown file", "nitpick_section.html#nitpick-files")}

    absent = fields.Dict(fields.NonEmptyString, fields.String())
    present = fields.Dict(fields.NonEmptyString, fields.String())
    # TODO: load this schema dynamically, then add this next field setup_cfg
    setup_cfg = fields.Nested(SetupCfgSchema, data_key="setup.cfg")


class NitpickSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick]`` section on the style file."""

    minimum_version = fields.NonEmptyString()
    styles = fields.Nested(NitpickStylesSectionSchema)
    files = fields.Nested(NitpickFilesSectionSchema)


class BaseStyleSchema(Schema):
    """Base validation schema for style files. Dynamic fields will be added to it later."""

    error_messages = {"unknown": help_message("Unknown file", "plugins.html")}

    nitpick = fields.Nested(NitpickSectionSchema)
