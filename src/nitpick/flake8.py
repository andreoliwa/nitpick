"""Flake8 plugin to check files."""
import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import attr
from flake8.options.manager import OptionManager
from loguru import logger

from nitpick import __version__
from nitpick.constants import FLAKE8_PREFIX, PROJECT_NAME
from nitpick.core import Nitpick
from nitpick.enums import OptionEnum
from nitpick.exceptions import QuitComplainingError
from nitpick.project import find_main_python_file
from nitpick.typedefs import Flake8Error
from nitpick.violations import Fuss


@attr.s(hash=False)
class NitpickFlake8Extension:
    """Main class for the flake8 extension."""

    # Plugin config
    name = PROJECT_NAME
    version = __version__

    # Plugin arguments passed by Flake8
    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    def run(self) -> Iterator[Flake8Error]:
        """Run the check plugin."""
        try:
            for collected_fuss in self.collect_errors():
                yield self.build_flake8_error(collected_fuss)
        except QuitComplainingError as err:
            for error_fuss in err.violations:
                yield self.build_flake8_error(error_fuss)

    def build_flake8_error(self, obj: Fuss) -> Flake8Error:
        """Return a flake8 error from a fuss."""
        prefix = f"File {obj.filename}" if obj.filename else ""
        line = f"{FLAKE8_PREFIX}{obj.code:03} {prefix}{obj.message}{obj.colored_suggestion}"
        return 0, 0, line, self.__class__

    def collect_errors(self) -> Iterator[Fuss]:
        """Collect all possible Nitpick errors."""
        nit = Nitpick.singleton()

        current_python_file = Path(self.filename)
        main_python_file: Path = find_main_python_file(nit.project.root)
        if current_python_file.absolute() != main_python_file.absolute():
            # Only report warnings once, for the main Python file of this project.
            logger.debug("Ignoring other Python file: {}", self.filename)
            return []

        logger.debug("Nitpicking file through flake8: {}", self.filename)
        yield from nit.run()
        return []

    @staticmethod
    @lru_cache()  # To avoid calling this function twice in the same process
    def add_options(option_manager: OptionManager):
        """Add the offline option."""
        option_manager.add_option(
            OptionEnum.OFFLINE.as_flake8_flag(), action="store_true", help=OptionEnum.OFFLINE.value
        )

    @staticmethod
    def parse_options(option_manager: OptionManager, options, args):  # pylint: disable=unused-argument
        """Create the Nitpick app, set logging from the verbose flags, set offline mode.

        This function is called only once by flake8, so it's a good place to create the app.
        """
        log_mapping = {1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(level=log_mapping.get(options.verbose, logging.WARNING))

        nit = Nitpick.singleton().init(offline=bool(options.nitpick_offline or OptionEnum.OFFLINE.get_environ()))
        logger.info("Offline mode: {}", nit.offline)
