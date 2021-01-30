"""Configuration of the plugin."""
import logging
from pathlib import Path
from typing import Iterator, Optional

from pluggy import PluginManager

from nitpick.constants import NITPICK_MINIMUM_VERSION_JMEX, PYPROJECT_TOML, TOOL_NITPICK, TOOL_NITPICK_JMEX
from nitpick.exceptions import MinimumVersionError, NitpickError, StyleError
from nitpick.formats import TOMLFormat
from nitpick.generic import search_dict, version_to_tuple
from nitpick.schemas import ToolNitpickSectionSchema, flatten_marshmallow_errors
from nitpick.style import Style
from nitpick.typedefs import JsonDict, StrOrList

LOGGER = logging.getLogger(__name__)


class Config:  # FIXME[AA]: Merge Config class into Project class
    """Plugin configuration, read from the project config."""

    def __init__(self, project_root: Path, plugin_manager: PluginManager) -> None:
        self.project_root: Path = project_root
        self.plugin_manager: PluginManager = plugin_manager

        self.pyproject_toml: Optional[TOMLFormat] = None
        self.tool_nitpick_dict: JsonDict = {}
        self.style_dict: JsonDict = {}
        self.nitpick_section: JsonDict = {}
        self.nitpick_files_section: JsonDict = {}

    def validate_pyproject_tool_nitpick(self) -> None:
        """Validate the ``pyroject.toml``'s ``[tool.nitpick]`` section against a Marshmallow schema."""
        # pylint: disable=import-outside-toplevel
        pyproject_path: Path = self.project_root / PYPROJECT_TOML
        if not pyproject_path.exists():
            return

        self.pyproject_toml = TOMLFormat(path=pyproject_path)
        self.tool_nitpick_dict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_toml.as_data, {})
        pyproject_errors = ToolNitpickSectionSchema().validate(self.tool_nitpick_dict)
        if not pyproject_errors:
            return

        raise StyleError(
            PYPROJECT_TOML, f"Invalid data in [{TOOL_NITPICK}]:", flatten_marshmallow_errors(pyproject_errors)
        )

    def merge_styles(self) -> Iterator[NitpickError]:
        """Merge one or multiple style files."""
        try:
            self.validate_pyproject_tool_nitpick()
        except StyleError as err:
            # If the project is misconfigured, don't even continue.
            yield err
            return

        configured_styles: StrOrList = self.tool_nitpick_dict.get("style", "")
        style = Style(self.project_root, self.plugin_manager)
        yield from style.find_initial_styles(configured_styles)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickExtension  # pylint: disable=import-outside-toplevel

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        if minimum_version and version_to_tuple(NitpickExtension.version) < version_to_tuple(minimum_version):
            yield MinimumVersionError(minimum_version, NitpickExtension.version)

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})
