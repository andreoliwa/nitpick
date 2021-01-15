"""Configuration of the plugin."""
import logging
from typing import TYPE_CHECKING, Optional

from identify import identify

from nitpick.app import NitpickApp
from nitpick.constants import NITPICK_MINIMUM_VERSION_JMEX, PROJECT_NAME, TOOL_NITPICK, TOOL_NITPICK_JMEX
from nitpick.exceptions import Deprecation
from nitpick.formats import TOMLFormat
from nitpick.generic import search_dict, version_to_tuple
from nitpick.mixin import NitpickMixin
from nitpick.plugins.pyproject_toml import PyProjectTomlPlugin
from nitpick.schemas import ToolNitpickSectionSchema, flatten_marshmallow_errors
from nitpick.style import Style
from nitpick.typedefs import YieldFlake8Error

if TYPE_CHECKING:
    from pathlib import Path

    from nitpick.typedefs import JsonDict, StrOrList

LOGGER = logging.getLogger(__name__)


class Config(NitpickMixin):  # pylint: disable=too-many-instance-attributes
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    def __init__(self) -> None:

        self.pyproject_toml = None  # type: Optional[TOMLFormat]
        self.tool_nitpick_dict = {}  # type: JsonDict
        self.style_dict = {}  # type: JsonDict
        self.nitpick_section = {}  # type: JsonDict
        self.nitpick_files_section = {}  # type: JsonDict

    def validate_pyproject_tool_nitpick(self) -> bool:
        """Validate the ``pyroject.toml``'s ``[tool.nitpick]`` section against a Marshmallow schema."""
        pyproject_path = NitpickApp.current().root_dir / PyProjectTomlPlugin.file_name  # type: Path
        if pyproject_path.exists():
            self.pyproject_toml = TOMLFormat(path=pyproject_path)
            self.tool_nitpick_dict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_toml.as_data, {})
            pyproject_errors = ToolNitpickSectionSchema().validate(self.tool_nitpick_dict)
            if pyproject_errors:
                NitpickApp.current().add_style_error(
                    PyProjectTomlPlugin.file_name,
                    "Invalid data in [{}]:".format(TOOL_NITPICK),
                    flatten_marshmallow_errors(pyproject_errors),
                )
                return False
        return True

    def merge_styles(self) -> YieldFlake8Error:
        """Merge one or multiple style files."""
        if not self.validate_pyproject_tool_nitpick():
            # If the project is misconfigured, don't even continue.
            return

        configured_styles = self.tool_nitpick_dict.get("style", "")  # type: StrOrList
        style = Style()
        style.find_initial_styles(configured_styles)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickExtension  # pylint: disable=import-outside-toplevel

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        if minimum_version and version_to_tuple(NitpickExtension.version) < version_to_tuple(minimum_version):
            yield self.flake8_error(
                3,
                "The style file you're using requires {}>={}".format(PROJECT_NAME, minimum_version)
                + " (you have {}). Please upgrade".format(NitpickExtension.version),
            )

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})


class FileNameCleaner:  # pylint: disable=too-few-public-methods
    """Clean the file name and get its tags."""

    def __init__(self, path_from_root: str) -> None:
        if Deprecation.pre_commit_without_dash(path_from_root):
            self.path_from_root = "." + path_from_root
        else:
            self.path_from_root = "." + path_from_root[1:] if path_from_root.startswith("-") else path_from_root
        self.tags = identify.tags_from_filename(path_from_root)
