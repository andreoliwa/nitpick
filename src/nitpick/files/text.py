"""Text files."""
import json
import logging

from nitpick import fields
from nitpick.files.base import BaseFile
from nitpick.schemas import BaseNitpickSchema
from nitpick.typedefs import YieldFlake8Error

LOGGER = logging.getLogger(__name__)


class LineSchema(BaseNitpickSchema):
    line = fields.String()


class TextFileSchema(BaseNitpickSchema):
    """Validation schema for any JSON file added to the style."""

    contains = fields.List(fields.Nested(LineSchema))


class TextFile(BaseFile):
    """Checker for any text file."""

    has_multiple_files = True
    error_base_number = 350

    nested_field = TextFileSchema
    identify_tags = {"text"}

    def suggest_initial_contents(self) -> str:
        x = self.file_path

    def check_rules(self) -> YieldFlake8Error:
        x = self.file_path
