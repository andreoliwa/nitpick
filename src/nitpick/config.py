"""Configuration of the plugin."""
import logging
from pathlib import Path
from typing import Optional

from nitpick import Nitpick
from nitpick.constants import (
    MERGED_STYLE_TOML,
    NITPICK_MINIMUM_VERSION_JMEX,
    PROJECT_NAME,
    TOOL_NITPICK,
    TOOL_NITPICK_JMEX,
)
from nitpick.exceptions import StyleError
from nitpick.files.pyproject_toml import PyProjectTomlFile
from nitpick.formats import TomlFormat
from nitpick.generic import search_dict, version_to_tuple
from nitpick.mixin import NitpickMixin
from nitpick.schemas import ToolNitpickSchema, flatten_marshmallow_errors
from nitpick.style import Style
from nitpick.typedefs import JsonDict, StrOrList, YieldFlake8Error

LOGGER = logging.getLogger(__name__)


class Config(NitpickMixin):  # pylint: disable=too-many-instance-attributes
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    def __init__(self) -> None:

        self.pyproject_toml = None  # type: Optional[TomlFormat]
        self.tool_nitpick_dict = {}  # type: JsonDict
        self.style_dict = {}  # type: JsonDict
        self.nitpick_section = {}  # type: JsonDict
        self.nitpick_files_section = {}  # type: JsonDict

    def validate_pyproject(self):
        """Validate the pyroject.toml against a Marshmallow schema."""
        pyproject_path = Nitpick.current_app().root_dir / PyProjectTomlFile.file_name  # type: Path
        if pyproject_path.exists():
            self.pyproject_toml = TomlFormat(path=pyproject_path)
            self.tool_nitpick_dict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_toml.as_data, {})
            pyproject_errors = ToolNitpickSchema().validate(self.tool_nitpick_dict)
            if pyproject_errors:
                raise StyleError(PyProjectTomlFile.file_name, flatten_marshmallow_errors(pyproject_errors))

    def merge_styles(self) -> YieldFlake8Error:
        """Merge one or multiple style files."""
        try:
            self.validate_pyproject()
        except StyleError as err:
            yield self.style_error(err.style_file_name, "Invalid data in [{}]:".format(TOOL_NITPICK), err.args[0])
            return

        configured_styles = self.tool_nitpick_dict.get("style", "")  # type: StrOrList
        style = Style()
        try:
            style.find_initial_styles(configured_styles)
        except StyleError as err:
            yield self.style_error(err.style_file_name, "Invalid TOML:", err.args[0])

        self.style_dict = style.merge_toml_dict()
        try:
            style.validate_style(MERGED_STYLE_TOML, self.style_dict)
        except StyleError as err:
            yield self.style_error(err.style_file_name, "Invalid data in the merged style file:", err.args[0])
            return

        from nitpick.plugin import NitpickChecker

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        if minimum_version and version_to_tuple(NitpickChecker.version) < version_to_tuple(minimum_version):
            yield self.flake8_error(
                3,
                "The style file you're using requires {}>={}".format(PROJECT_NAME, minimum_version)
                + " (you have {}). Please upgrade".format(NitpickChecker.version),
            )

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})
