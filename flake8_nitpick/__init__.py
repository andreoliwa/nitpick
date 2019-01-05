"""Main package."""
import itertools
import logging
from configparser import ConfigParser
from io import StringIO
from typing import Optional, Tuple, Type, Any, Dict, Generator, List

import os
import dictdiffer
import attr
from pathlib import Path

import requests
import toml

from flake8_nitpick.__version__ import __version__
from flake8_nitpick.generic import get_subclasses, flatten, unflatten, climb_directory_tree

# Types
Flake8Error = Tuple[int, int, str, Type]
YieldFlake8Error = Generator[Flake8Error, Any, Any]

# Constants
NAME = "flake8-nitpick"
ERROR_PREFIX = "NIP"
CACHE_DIR: Path = Path(os.getcwd()) / ".cache" / NAME
PYPROJECT_TOML = "pyproject.toml"
NITPICK_STYLE_TOML = "nitpick-style.toml"
DEFAULT_NITPICK_STYLE_URL = "https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml"
ROOT_PYTHON_FILES = ("setup.py", "manage.py", "autoapp.py")
ROOT_FILES = (PYPROJECT_TOML, "setup.cfg", "requirements*.txt", "Pipfile") + ROOT_PYTHON_FILES

LOG = logging.getLogger("flake8.nitpick")


class NitpickMixin:
    """A helper mixin to raise flake8 errors."""

    error_base_number: int = 0
    error_prefix: str = ""

    def flake8_error(self, error_number: int, error_message: str, error_base_number: int = None) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        final_number = (error_base_number or self.error_base_number) + error_number
        return 1, 0, f"{ERROR_PREFIX}{final_number} {self.error_prefix}{error_message}", NitpickChecker


class NitpickCache:
    """A cache file in the current dir (in .toml format), to store data that will be reused by the plugin."""

    def __init__(self, key: str) -> None:
        """Init the cache file."""
        self.cache_file: Path = CACHE_DIR / "variables.toml"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_file.touch(exist_ok=True)
        self.toml_dict = toml.load(str(self.cache_file))

        self.key = key

    def load(self) -> Optional[str]:
        """Load the key from the cache file."""
        return self.toml_dict.get(self.key)

    def load_path(self) -> Optional[Path]:
        """Load the key and resolve the path."""
        value = self.load()
        if value is None:
            return value
        return Path(value).resolve()

    def dump(self, value: Any) -> Any:
        """Save the value (as a string) to the cache file."""
        self.toml_dict[self.key] = str(value)
        toml.dump(self.toml_dict, self.cache_file.open("w"))
        return value

    def dump_path(self, path: Path) -> Path:
        """Save the path relative to the current working dir."""
        try:
            value = path.resolve().relative_to(os.getcwd())
        except ValueError:
            # If the path is outside the current directory, use the absolute path.
            value = path.resolve()
        self.dump(value)
        return path


class NitpickConfig(NitpickMixin):
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    pyproject_path: Path
    pyproject_toml: dict
    tool_nitpick_toml: dict
    style_toml: dict
    files: dict

    def __init__(self, root_dir: Path) -> None:
        """Init instance."""
        self.root_dir = root_dir

    def load_toml(self) -> YieldFlake8Error:
        """Load TOML configuration from files."""
        self.pyproject_path: Path = self.root_dir / PYPROJECT_TOML
        self.pyproject_toml = toml.load(str(self.pyproject_path))
        self.tool_nitpick_toml = self.pyproject_toml.get("tool", {}).get("nitpick", {})

        try:
            style_path = self.find_style()
        except FileNotFoundError as err:
            yield self.flake8_error(2, str(err))
            return
        self.style_toml = toml.load(str(style_path))

        self.files: Dict[str, bool] = self.style_toml.get("files", {})

    def find_style(self) -> Optional[Path]:
        """Search for a style file."""
        cache = NitpickCache("style")
        style_path = cache.load_path()
        if style_path is not None:
            LOG.info("Loading cached style: %s", style_path)
            return style_path

        style: str = self.tool_nitpick_toml.get("style", "")
        if style.startswith("http"):
            # If the style is a URL, save the contents in the cache dir
            style_path = self.load_style_from_url(style)
            LOG.info("Loading style from URL: %s", style_path)
        elif style:
            style_path = Path(style)
            if not style_path.exists():
                raise FileNotFoundError(f"Style file does not exist: {style}")
            LOG.info("Loading style from file: %s", style_path)
        else:
            paths = climb_directory_tree(self.root_dir, [NITPICK_STYLE_TOML])
            if paths:
                style_path = paths[0]
                LOG.info("Loading style from directory tree: %s", style_path)
            else:
                style_path = self.load_style_from_url(DEFAULT_NITPICK_STYLE_URL)
                LOG.info("Loading default Nitpick style %s into local file %s", DEFAULT_NITPICK_STYLE_URL, style_path)

        cache.dump_path(style_path)
        return style_path

    @staticmethod
    def load_style_from_url(url: str) -> Path:
        """Load a style file from a URL."""
        response = requests.get(url)
        if not response.ok:
            raise FileNotFoundError(f"Error {response} fetching style URL {url}")
        contents = response.text
        style_path = CACHE_DIR / "style.toml"
        style_path.write_text(contents)
        return style_path

    def check_absent_files(self) -> YieldFlake8Error:
        """Check absent files."""
        for file_dict in self.files.get("absent", []):
            file_name = file_dict.get("file")
            if not file_name:
                continue

            file: Path = self.root_dir / file_name
            if not file.exists():
                continue

            config_message = file_dict.get("message")
            full_message = f"File {file_name} should be deleted"
            if config_message:
                full_message += f": {config_message}"

            yield self.flake8_error(1, full_message)


@attr.s(hash=False)
class NitpickChecker(NitpickMixin):
    """Main plugin class."""

    # Plugin config
    name = NAME
    version = __version__

    # Plugin arguments passed by Flake8
    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    # NitpickMixin
    error_base_number = 100

    def run(self) -> YieldFlake8Error:
        """Run the check plugin."""
        root_dir = self.find_root_dir(self.filename)
        if not root_dir:
            yield self.flake8_error(1, "No root dir found (is this a Python project?)")
            return

        current_python_file = Path(self.filename)
        main_python_file = self.find_main_python_file(root_dir, current_python_file)
        if not main_python_file:
            yield self.flake8_error(2, f"No Python file was found in the root dir {root_dir}")
            return
        if current_python_file.resolve() != main_python_file.resolve():
            # Only report warnings once, for the main Python file of this project.
            return

        config = NitpickConfig(root_dir)
        for error in itertools.chain(config.load_toml(), config.check_absent_files()):
            yield error

        for checker_class in get_subclasses(BaseChecker):
            checker = checker_class(config)
            for error in itertools.chain(checker.check_exists(), checker.check_rules()):
                yield error

        return []

    @staticmethod
    def find_root_dir(python_file: str) -> Optional[Path]:
        """Find the root dir of the Python project: the dir that has one of the `ROOT_FILES`."""
        cache = NitpickCache("root_dir")
        root_dir = cache.load_path()
        if root_dir is not None:
            LOG.info("Loading cached root dir: %s", root_dir)
            return root_dir

        found_files = climb_directory_tree(python_file, ROOT_FILES)
        if not found_files:
            LOG.error("No files found while climbing directory tree from %s", python_file)
            return None
        root_dir = found_files[0].parent
        cache.dump_path(root_dir)
        return root_dir

    def find_main_python_file(self, root_dir: Path, current_file: Path) -> Path:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings."""
        cache = NitpickCache("main_python_file")
        main_python_file = cache.load_path()
        if main_python_file is not None:
            LOG.info("Loading cached main Python file: %s", main_python_file)
            return main_python_file

        for the_file in itertools.chain(
            [root_dir / root_file for root_file in ROOT_PYTHON_FILES], root_dir.glob("*.py")
        ):
            if the_file.exists():
                found = the_file
                LOG.info("Found the file %s", the_file)
                break
        else:
            LOG.info("Using current file as main file %s", current_file)
            found = current_file
        return cache.dump_path(found)


class BaseChecker(NitpickMixin):
    """Base class for file checkers."""

    file_name: str
    error_base_number = 300

    def __init__(self, config: NitpickConfig) -> None:
        """Init instance."""
        self.config = config
        self.file_path: Path = self.config.root_dir / self.file_name
        self.file_toml = self.config.style_toml.get(self.file_name, {})
        self.error_prefix = f"File: {self.file_name}: "

    def check_exists(self) -> YieldFlake8Error:
        """Check if the file should exist; if there is style configuration for the file, then it should exist."""
        should_exist: bool = self.config.files.get(self.file_name, bool(self.file_toml))
        file_exists = self.file_path.exists()

        if should_exist and not file_exists:
            yield self.flake8_error(1, f"Missing file")
        elif not should_exist and file_exists:
            yield self.flake8_error(2, f"File should be deleted")

    def check_rules(self) -> YieldFlake8Error:
        """Check rules for this file. It should be overridden by inherited class if they need."""
        return []


class PyProjectTomlChecker(BaseChecker):
    """Check pyproject.toml."""

    file_name = "pyproject.toml"
    error_base_number = 310

    def check_rules(self) -> YieldFlake8Error:
        """Check missing key/value pairs in pyproject.toml."""
        actual = flatten(self.config.pyproject_toml)
        expected = flatten(self.file_toml)
        if expected.items() <= actual.items():
            return []

        missing_dict = unflatten({k: v for k, v in expected.items() if k not in actual})
        if missing_dict:
            missing_toml = toml.dumps(missing_dict)
            yield self.flake8_error(1, f"Missing values:\n{missing_toml}")

        diff_dict = unflatten({k: v for k, v in expected.items() if k in actual and expected[k] != actual[k]})
        if diff_dict:
            diff_toml = toml.dumps(diff_dict)
            yield self.flake8_error(2, f"Different values:\n{diff_toml}")


class SetupCfgChecker(BaseChecker):
    """Check setup.cfg."""

    file_name = "setup.cfg"
    error_base_number = 320

    COMMA_SEPARATED_KEYS = {"flake8.ignore"}

    def check_rules(self) -> YieldFlake8Error:
        """Check missing sections and missing key/value pairs in setup.cfg."""
        setup_cfg = ConfigParser()
        setup_cfg.read_file(self.file_path.open())

        actual_sections = set(setup_cfg.sections())
        expected_sections = set(self.file_toml.keys())
        missing_sections = expected_sections - actual_sections

        if missing_sections:
            missing_cfg = ConfigParser()
            for section in missing_sections:
                missing_cfg[section] = self.file_toml[section]
            output = self.get_example_cfg(missing_cfg)
            yield self.flake8_error(2, f"Missing sections:\n{output}")

        generators = []
        for section in expected_sections - missing_sections:
            expected_dict = self.file_toml[section]
            actual_dict = dict(setup_cfg[section])
            for diff_type, key, values in dictdiffer.diff(expected_dict, actual_dict):
                if diff_type == dictdiffer.CHANGE:
                    generators.append(self.compare_different_keys(section, key, values[0], values[1]))
                elif diff_type == dictdiffer.REMOVE:
                    generators.append(self.show_missing_keys(section, key, values))
        for error in itertools.chain(*generators):
            yield error

    def compare_different_keys(self, section, key, raw_expected, raw_actual):
        """Compare different keys, with special treatment when they are lists or numeric."""
        combined = f"{section}.{key}"
        if combined in self.COMMA_SEPARATED_KEYS:
            # The values might contain spaces
            actual = {s.strip() for s in raw_actual.split(",")}
            expected = {s.strip() for s in raw_expected.split(",")}
            missing = expected - actual
            if missing:
                yield self.flake8_error(3, f"Missing values in key\n[{section}]\n{key} = {','.join(sorted(missing))}")
            return

        if isinstance(raw_actual, (int, float, bool)) or isinstance(raw_expected, (int, float, bool)):
            # A boolean "True" or "true" has the same effect on setup.cfg.
            actual = str(raw_actual).lower()
            expected = str(raw_expected).lower()
        else:
            actual = raw_actual
            expected = raw_expected
        if actual != expected:
            yield self.flake8_error(
                4, f"Expected value {raw_expected!r} in key, got {raw_actual!r}\n[{section}]\n{key} = {raw_expected}"
            )

    def show_missing_keys(self, section, key, values: List[Tuple[str, Any]]):
        """Show the keys that are not present in a section."""
        missing_cfg = ConfigParser()
        missing_cfg[section] = dict(values)
        output = self.get_example_cfg(missing_cfg)
        yield self.flake8_error(5, f"Missing keys in section:\n{output}")

    @staticmethod
    def get_example_cfg(config_parser: ConfigParser) -> str:
        """Print an example of a config parser in a string instead of a file."""
        string_stream = StringIO()
        config_parser.write(string_stream)
        output = string_stream.getvalue().strip()
        return output
