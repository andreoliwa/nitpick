"""Text files."""
from typing import Iterator, Optional, Type

from marshmallow import Schema
from marshmallow.orderedset import OrderedSet

from nitpick import fields
from nitpick.exceptions import NitpickError
from nitpick.plugins import hookimpl
from nitpick.plugins.base import FileData, NitpickPlugin
from nitpick.schemas import help_message

TEXT_FILE_RTFD_PAGE = "plugins.html#text-files"


class TextItemSchema(Schema):
    """Validation schema for the object inside ``contains``."""

    error_messages = {"unknown": help_message("Unknown configuration", TEXT_FILE_RTFD_PAGE)}
    line = fields.NonEmptyString()


class TextSchema(Schema):
    """Validation schema for the text file TOML configuration."""

    error_messages = {"unknown": help_message("Unknown configuration", TEXT_FILE_RTFD_PAGE)}
    contains = fields.List(fields.Nested(TextItemSchema))


class TextError(NitpickError):
    """Base for text file errors."""

    error_base_number = 350


class TextPlugin(NitpickPlugin):
    """Enforce configuration on text files.

    To check if ``some.txt`` file contains the lines ``abc`` and ``def`` (in any order):

    .. code-block:: toml

        [["some.txt".contains]]
        line = "abc"

        [["some.txt".contains]]
        line = "def"
    """

    error_class = TextError
    identify_tags = {"text"}
    validation_schema = TextSchema

    #: All other files are also text files, and they already have a suggested content message
    # TODO: this is a hack to avoid rethinking the whole schema validation now (this will have to be done some day)
    skip_empty_suggestion = True

    def _expected_lines(self):
        return [obj.get("line") for obj in self.file_dict.get("contains", {})]

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return "\n".join(self._expected_lines())

    def enforce_rules(self) -> Iterator[NitpickError]:
        """Enforce rules for missing lines."""
        expected = OrderedSet(self._expected_lines())
        actual = OrderedSet(self.file_path.read_text().split("\n"))
        missing = expected - actual
        if missing:
            yield TextError(" has missing lines:", "\n".join(sorted(missing)), 2)


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return TextPlugin


@hookimpl
def can_handle(data: FileData) -> Optional["NitpickPlugin"]:
    """Handle text files."""
    if TextPlugin.identify_tags & data.tags:
        return TextPlugin(data)
    return None
