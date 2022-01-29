"""Text files."""
from __future__ import annotations

from typing import Iterator

from marshmallow import Schema
from marshmallow.orderedset import OrderedSet

from nitpick import fields
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.schemas import help_message
from nitpick.violations import Fuss, ViolationEnum

TEXT_FILE_RTFD_PAGE = "plugins.html#text-files"
KEY_CONTAINS = "contains"


class TextItemSchema(Schema):
    """Validation schema for the object inside ``contains``."""

    error_messages = {"unknown": help_message("Unknown configuration", TEXT_FILE_RTFD_PAGE)}
    line = fields.NonEmptyString()


class TextSchema(Schema):
    """Validation schema for the text file TOML configuration."""

    error_messages = {"unknown": help_message("Unknown configuration", TEXT_FILE_RTFD_PAGE)}
    contains = fields.List(fields.Nested(TextItemSchema))


class Violations(ViolationEnum):
    """Violations for this plugin."""

    MISSING_LINES = (352, " has missing lines:")


class TextPlugin(NitpickPlugin):
    """Enforce configuration on text files.

    To check if ``some.txt`` file contains the lines ``abc`` and ``def`` (in any order):

    .. code-block:: toml

        [["some.txt".contains]]
        line = "abc"

        [["some.txt".contains]]
        line = "def"
    """

    identify_tags = {"text"}
    validation_schema = TextSchema

    #: All other files are also text files, and they already have a suggested content message
    # TODO: refactor: rethink the whole schema validation and remove this attribute
    skip_empty_suggestion = True

    violation_base_code = 350

    def _expected_lines(self):
        return [obj.get("line") for obj in self.expected_config.get(KEY_CONTAINS, {})]

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return "\n".join(self._expected_lines())

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing lines."""
        expected = OrderedSet(self._expected_lines())
        actual = OrderedSet(self.file_path.read_text().split("\n"))
        missing = expected - actual
        if missing:
            yield self.reporter.make_fuss(Violations.MISSING_LINES, "\n".join(sorted(missing)))


@hookimpl
def plugin_class() -> type[NitpickPlugin]:
    """Handle text files."""
    return TextPlugin


@hookimpl
def can_handle(info: FileInfo) -> type[NitpickPlugin] | None:
    """Handle text files."""
    if TextPlugin.identify_tags & info.tags:
        return TextPlugin
    return None
