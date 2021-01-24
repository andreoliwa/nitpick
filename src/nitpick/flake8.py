"""Flake8 plugin to check files."""
import itertools
import logging
from pathlib import Path

import attr
from flake8.options.manager import OptionManager

from nitpick import __version__
from nitpick.app import NitpickApp
from nitpick.cli import NitpickFlags
from nitpick.constants import PROJECT_NAME
from nitpick.mixin import NitpickMixin
from nitpick.plugins.base import FilePathTags
from nitpick.typedefs import YieldFlake8Error

LOGGER = logging.getLogger(__name__)


@attr.s(hash=False)
class NitpickExtension(NitpickMixin):
    """Main class for the flake8 extension."""

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
        app = NitpickApp.current()
        for err in app.init_errors:
            has_errors = True
            yield NitpickApp.as_flake8_warning(err)
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
            yield NitpickApp.as_flake8_warning(err)
        if has_errors:
            return []

        # Get all root keys from the merged style.
        for config_key, config_dict in app.config.style_dict.items():
            # All except "nitpick" are file names.
            if config_key == PROJECT_NAME:
                continue

            # For each file name, find the plugin(s) that can handle the file.
            for plugin_instance in app.plugin_manager.hook.can_handle(  # pylint: disable=no-member
                file=FilePathTags(config_key)
            ):
                yield from plugin_instance.process(config_dict)

        return []

    def check_files(self, present: bool) -> YieldFlake8Error:
        """Check files that should be present or absent."""
        key = "present" if present else "absent"
        message = "exist" if present else "be deleted"
        absent = not present
        for file_name, extra_message in NitpickApp.current().config.nitpick_files_section.get(key, {}).items():
            file_path = NitpickApp.current().root_dir / file_name  # type: Path
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
            NitpickApp.format_flag(NitpickFlags.OFFLINE),
            action="store_true",
            # dest="offline",
            help=NitpickFlags.OFFLINE.value,
        )

    @staticmethod
    def parse_options(option_manager: OptionManager, options, args):  # pylint: disable=unused-argument
        """Create the Nitpick app, set logging from the verbose flags, set offline mode.

        This function is called only once by flake8, so it's a good place to create the app.
        """
        log_mapping = {1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(level=log_mapping.get(options.verbose, logging.WARNING))

        NitpickApp.create_app(offline=bool(options.nitpick_offline or NitpickApp.get_env(NitpickFlags.OFFLINE)))
        LOGGER.info("Offline mode: %s", NitpickApp.current().offline)
