"""Flake8 plugin to check files."""
# pylint: disable=too-few-public-methods,import-outside-toplevel
# FIXME: remove this disabled warning
import itertools
import logging
from pathlib import Path
from typing import Optional, Set

import attr
import pluggy
from flake8.options.manager import OptionManager
from identify import identify
from pluggy import PluginManager

from nitpick import __version__
from nitpick.app import Nitpick
from nitpick.constants import PROJECT_NAME
from nitpick.files.base import BaseFile
from nitpick.formats import TomlFormat
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import YieldFlake8Error

hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)

LOGGER = logging.getLogger(__name__)


class NitpickPlugin:
    """Base for a Nitpick plugin."""

    base_file = None  # type: BaseFile

    @hookspec
    def handle(self, filename: str, tags: Set[str]) -> Optional["NitpickPlugin"]:
        """Return self if this plugin handle the relative filename or any of its :py:package:`identify` tags."""


class TextPlugin(NitpickPlugin):
    """Handle text files."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle text files."""
        from nitpick.files.text import TextFile

        self.base_file = TextFile(filename)
        return self if "plain-text" in tags else None


class JSONPlugin(NitpickPlugin):
    """Handle JSON files."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle JSON files."""
        from nitpick.files.json import JSONFile

        self.base_file = JSONFile()
        return self if "json" in tags else None


class PreCommitPlugin(NitpickPlugin):
    """Handle pre-commit config file."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle pre-commit config file."""
        from nitpick.files.pre_commit import PreCommitFile

        self.base_file = PreCommitFile()
        return self if filename == TomlFormat.group_name_for(self.base_file.file_name) else None


class SetupCfgPlugin(NitpickPlugin):
    """Handle setup.cfg files."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle setup.cfg files."""
        from nitpick.files.setup_cfg import SetupCfgFile

        self.base_file = SetupCfgFile()
        return self if filename == SetupCfgFile.file_name else None


class PyProjectTomlPlugin(NitpickPlugin):
    """Handle pyproject.toml file."""

    @hookimpl
    def handle(self, filename: str, tags: Set[str]) -> Optional[NitpickPlugin]:
        """Handle pyproject.toml file."""
        from nitpick.files.pyproject_toml import PyProjectTomlFile

        self.base_file = PyProjectTomlFile()
        return self if filename == self.base_file.file_name else None


@attr.s(hash=False)
class NitpickChecker(NitpickMixin):
    """Main plugin class."""

    # Plugin config
    name = PROJECT_NAME
    version = __version__

    # NitpickMixin
    error_base_number = 100

    # Plugin arguments passed by Flake8
    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    def run(self) -> YieldFlake8Error:
        """Run the check plugin."""
        has_errors = False
        app = Nitpick.current_app()
        for err in app.init_errors:
            has_errors = True
            yield Nitpick.as_flake8_warning(err)
        if has_errors:
            return []

        current_python_file = Path(self.filename)
        if current_python_file.absolute() != app.main_python_file.absolute():
            # Only report warnings once, for the main Python file of this project.
            LOGGER.debug("Ignoring file: %s", self.filename)
            return []
        LOGGER.debug("Nitpicking file: %s", self.filename)

        yield from itertools.chain(app.config.merge_styles(), self.check_files(True), self.check_files(False))

        has_errors = False
        for err in app.style_errors:
            has_errors = True
            yield Nitpick.as_flake8_warning(err)
        if has_errors:
            return []

        plugin_manager = self.load_plugins()

        # Get all root keys from the style TOML.
        for path in app.config.style_dict:
            # All except "nitpick" are file names.
            if path == PROJECT_NAME:
                continue

            # For each file name, find the plugin that can handle the file.
            tags = identify.tags_from_filename(path)
            for plugin in plugin_manager.hook.handle(  # pylint: disable=no-member
                filename=path, tags=tags
            ):  # type: NitpickPlugin
                yield from plugin.base_file.check_exists()

        return []

    @staticmethod
    def load_plugins() -> PluginManager:
        """Load all defined plugins."""
        plugin_manager = pluggy.PluginManager(PROJECT_NAME)
        plugin_manager.add_hookspecs(NitpickPlugin)

        # FIXME: use entry points instead
        plugin_manager.register(JSONPlugin())
        plugin_manager.register(TextPlugin())
        plugin_manager.register(PreCommitPlugin())
        plugin_manager.register(SetupCfgPlugin())
        plugin_manager.register(PyProjectTomlPlugin())

        return plugin_manager

    def check_files(self, present: bool) -> YieldFlake8Error:
        """Check files that should be present or absent."""
        key = "present" if present else "absent"
        message = "exist" if present else "be deleted"
        absent = not present
        for file_name, extra_message in Nitpick.current_app().config.nitpick_files_section.get(key, {}).items():
            file_path = Nitpick.current_app().root_dir / file_name  # type: Path
            exists = file_path.exists()
            if (present and exists) or (absent and not exists):
                continue

            full_message = "File {} should {}".format(file_name, message)
            if extra_message:
                full_message += ": {}".format(extra_message)

            yield self.flake8_error(3 if present else 4, full_message)

    @staticmethod
    def add_options(option_manager: OptionManager):
        """Add the offline option."""
        option_manager.add_option(
            Nitpick.format_flag(Nitpick.Flags.OFFLINE),
            action="store_true",
            # dest="offline",
            help=Nitpick.Flags.OFFLINE.value,
        )

    @staticmethod
    def parse_options(option_manager: OptionManager, options, args):  # pylint: disable=unused-argument
        """Create the Nitpick app, set logging from the verbose flags, set offline mode.

        This function is called only once by flake8, so it's a good place to create the app.
        """
        log_mapping = {1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(level=log_mapping.get(options.verbose, logging.WARNING))

        Nitpick.create_app(offline=bool(options.nitpick_offline or Nitpick.get_env(Nitpick.Flags.OFFLINE)))
        LOGGER.info("Offline mode: %s", Nitpick.current_app().offline)
