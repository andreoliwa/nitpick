"""Configuration of the plugin."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import Optional, Set

from nitpick.constants import (
    CACHE_DIR_NAME,
    MANAGE_PY,
    MERGED_STYLE_TOML,
    NITPICK_MINIMUM_VERSION_JMEX,
    PROJECT_NAME,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    TOOL_NITPICK,
    TOOL_NITPICK_JMEX,
)
from nitpick.exceptions import StyleError
from nitpick.files.base import BaseFile
from nitpick.files.pyproject_toml import PyProjectTomlFile
from nitpick.files.setup_cfg import SetupCfgFile
from nitpick.formats import TomlFormat
from nitpick.generic import climb_directory_tree, get_subclasses, search_dict, version_to_tuple
from nitpick.mixin import NitpickMixin
from nitpick.schemas import MergedStyleSchema, ToolNitpickSchema, flatten_marshmallow_errors
from nitpick.style import Style
from nitpick.typedefs import JsonDict, PathOrStr, StrOrList, YieldFlake8Error

LOGGER = logging.getLogger(__name__)


class NitpickConfig(NitpickMixin):  # pylint: disable=too-many-instance-attributes
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    _singleton_instance = None  # type: Optional["NitpickConfig"]

    def __init__(self) -> None:
        """Init instance."""
        self.main_python_file = Path()
        self.cache_dir = None  # type: Optional[Path]

        self.pyproject_toml = None  # type: Optional[TomlFormat]
        self.tool_nitpick_dict = {}  # type: JsonDict
        self.style_dict = {}  # type: JsonDict
        self.nitpick_dict = {}  # type: JsonDict
        self.files = {}  # type: JsonDict

    @classmethod
    def get_singleton(cls) -> "NitpickConfig":
        """Init the global singleton instance of the plugin configuration, needed by all file checkers."""
        if cls._singleton_instance is None:
            cls._singleton_instance = cls()
        return cls._singleton_instance

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance. Useful on automated tests, to simulate ``flake8`` execution."""
        cls._singleton_instance = None

    def find_root_dir(self, starting_file: PathOrStr) -> bool:
        """Find the root dir of the Python project: the dir that has one of the `ROOT_FILES`.

        Also clear the cache dir the first time the root dir is found.
        """
        if hasattr(self, "root_dir"):
            return True

        root_dirs = set()  # type: Set[Path]
        seen = set()  # type: Set[Path]

        starting_dir = Path(starting_file).parent.absolute()
        while True:
            project_files = climb_directory_tree(
                starting_dir, ROOT_FILES + (PyProjectTomlFile.file_name, SetupCfgFile.file_name)
            )
            if project_files and project_files & seen:
                break
            seen.update(project_files or [])

            if not project_files:
                # If none of the root files were found, try again with manage.py.
                # On Django projects, it can be in another dir inside the root dir.
                project_files = climb_directory_tree(starting_file, [MANAGE_PY])
                if not project_files or project_files & seen:
                    break
                seen.update(project_files)

            for found in project_files or []:
                root_dirs.add(found.parent)

            # Climb up one directory to search for more project files
            starting_dir = starting_dir.parent
            if not starting_dir:
                break

        if not root_dirs:
            LOGGER.error("No files found while climbing directory tree from %s", str(starting_file))
            return False

        # If multiple roots are found, get the top one (grandparent dir)
        self.root_dir = sorted(root_dirs)[0]  # pylint: disable=attribute-defined-outside-init
        self.clear_cache_dir()
        return True

    def find_main_python_file(self) -> bool:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

        The search order is:
        1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
        2. ``manage.py``: they can be on the root or on a subdir (Django projects).
        3. Any other ``*.py`` Python file.
        """
        if not self.root_dir:
            return False
        for the_file in itertools.chain(
            [self.root_dir / root_file for root_file in ROOT_PYTHON_FILES],
            self.root_dir.glob("*/{}".format(MANAGE_PY)),
            self.root_dir.glob("*/*.py"),
        ):
            if the_file.exists():
                self.main_python_file = Path(the_file)
                LOGGER.info("Found the file %s", the_file)
                return True
        return False

    def clear_cache_dir(self) -> None:
        """Clear the cache directory (on the project root or on the current directory)."""
        if not self.root_dir:
            return
        cache_root = self.root_dir / CACHE_DIR_NAME  # type: Path
        self.cache_dir = cache_root / PROJECT_NAME
        rmtree(str(self.cache_dir), ignore_errors=True)

    def validate_pyproject(self):
        """Validate the pyroject.toml against a Marshmallow schema."""
        pyproject_path = self.root_dir / PyProjectTomlFile.file_name  # type: Path
        if pyproject_path.exists():
            self.pyproject_toml = TomlFormat(path=pyproject_path)
            self.tool_nitpick_dict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_toml.as_data, {})
            pyproject_errors = ToolNitpickSchema().validate(self.tool_nitpick_dict)
            if pyproject_errors:
                raise StyleError(PyProjectTomlFile.file_name, flatten_marshmallow_errors(pyproject_errors))

    def validate_merged_style(self):
        """Validate the merged style file (TOML) against a Marshmallow schema."""
        validation_dict = self.style_dict.copy()
        for file_class in get_subclasses(BaseFile):
            root_keys_to_remove = []
            file_key = file_class().toml_key
            if file_key:
                root_keys_to_remove.append(file_key)
            root_keys_to_remove.extend(
                search_dict("nitpick.{}.file_names".format(file_class.__name__), validation_dict, [])
            )
            for key in root_keys_to_remove:
                if key in validation_dict:
                    validation_dict.pop(key)
        style_errors = MergedStyleSchema().validate(validation_dict)
        if style_errors:
            raise StyleError(MERGED_STYLE_TOML, flatten_marshmallow_errors(style_errors))

    def merge_styles(self) -> YieldFlake8Error:
        """Merge one or multiple style files."""
        try:
            self.validate_pyproject()
        except StyleError as err:
            yield self.style_error(err.style_file_name, "Invalid data in [{}]:".format(TOOL_NITPICK), err.args[0])
            return

        configured_styles = self.tool_nitpick_dict.get("style", "")  # type: StrOrList
        style = Style(self)
        try:
            style.find_initial_styles(configured_styles)
        except StyleError as err:
            yield self.style_error(err.style_file_name, "Invalid TOML:", err.args[0])

        self.style_dict = style.merge_toml_dict()
        try:
            self.validate_merged_style()
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

        self.nitpick_dict = self.style_dict.get("nitpick", {})
        self.files = self.nitpick_dict.get("files", {})
