"""Marshmallow schemas."""
from typing import Dict

from marshmallow import Schema
from marshmallow_polyfield import PolyField
from sortedcontainers import SortedDict

from nitpick import fields
from nitpick.constants import READ_THE_DOCS_URL
from nitpick.files.setup_cfg import SetupCfgFile
from nitpick.generic import flatten


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


def help_message(sentence: str, help_page: str) -> str:
    """Show help with the documentation URL on validation errors."""
    clean_sentence = sentence.strip(" .")
    return "{}. See {}{}.".format(clean_sentence, READ_THE_DOCS_URL, help_page)


class BaseNitpickSchema(Schema):
    """Base schema for all others, with default error messages."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html")}


class ToolNitpickSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[tool.nitpick]`` section on ``pyproject.toml``."""

    error_messages = {"unknown": help_message("Unknown configuration", "tool_nitpick_section.html")}

    style = PolyField(deserialization_schema_selector=fields.string_or_list_field)


class NitpickStylesSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick.styles]`` section on the style file."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html#nitpick-styles")}

    include = PolyField(deserialization_schema_selector=fields.string_or_list_field)


class NitpickJSONFileSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick.JSONFile]`` section on the style file."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html#nitpick-jsonfile")}

    file_names = fields.List(fields.String)


class SetupCfgSchema(BaseNitpickSchema):
    """Validation schema for setup.cfg."""

    error_messages = {"unknown": help_message("Unknown configuration", "nitpick_section.html#comma-separated-values")}

    comma_separated_values = fields.List(fields.String(validate=fields.validate_section_dot_field))


class NitpickFilesSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick.files]`` section on the style file."""

    error_messages = {"unknown": help_message("Unknown file", "nitpick_section.html#nitpick-files")}

    absent = fields.Dict(fields.FilledString, fields.String())
    present = fields.Dict(fields.FilledString, fields.String())
    # TODO: load this schema dynamically, then add this next field setup_cfg
    setup_cfg = fields.Nested(SetupCfgSchema, data_key=SetupCfgFile.file_name)


class NitpickSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[nitpick]`` section on the style file."""

    minimum_version = fields.FilledString()
    styles = fields.Nested(NitpickStylesSectionSchema)
    files = fields.Nested(NitpickFilesSectionSchema)
    # TODO: load this schema dynamically, then add this next field JSONFile
    JSONFile = fields.Nested(NitpickJSONFileSectionSchema)


class BaseStyleSchema(Schema):
    """Base validation schema for style files. Dynamic fields will be added to it later."""

    error_messages = {"unknown": help_message("Unknown file", "config_files.html")}

    nitpick = fields.Nested(NitpickSectionSchema)
