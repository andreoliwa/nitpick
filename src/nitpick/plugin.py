"""Flake8 plugin to check files."""
import itertools
import logging
from pathlib import Path

import attr
from flake8.options.manager import OptionManager

from nitpick import __version__
from nitpick.app import Nitpick
from nitpick.constants import PROJECT_NAME
from nitpick.files.base import BaseFile
from nitpick.generic import get_subclasses
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import YieldFlake8Error

LOGGER = logging.getLogger(__name__)


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
        for err in Nitpick.current_app().init_errors:
            has_errors = True
            yield Nitpick.as_flake8_warning(err)
        if has_errors:
            return []

        current_python_file = Path(self.filename)
        if current_python_file.absolute() != Nitpick.current_app().main_python_file.absolute():
            # Only report warnings once, for the main Python file of this project.
            LOGGER.debug("Ignoring file: %s", self.filename)
            return []
        LOGGER.debug("Nitpicking file: %s", self.filename)

        yield from itertools.chain(
            Nitpick.current_app().config.merge_styles(), self.check_files(True), self.check_files(False)
        )

        has_errors = False
        for err in Nitpick.current_app().style_errors:
            has_errors = True
            yield Nitpick.as_flake8_warning(err)
        if has_errors:
            return []

        for checker_class in get_subclasses(BaseFile):
            checker = checker_class()
            yield from checker.check_exists()

        return []

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
