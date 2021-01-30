"""Flake8 plugin to check files."""
import logging
from pathlib import Path
from typing import Iterator

import attr
from flake8.options.manager import OptionManager

from nitpick import __version__
from nitpick.cli import NitpickFlag
from nitpick.constants import PROJECT_NAME
from nitpick.core import Nitpick
from nitpick.exceptions import InitError, NitpickError, NoPythonFileError, NoRootDirError
from nitpick.plugins.base import FileData
from nitpick.typedefs import Flake8Error

LOGGER = logging.getLogger(__name__)


@attr.s(hash=False)
class NitpickExtension:
    """Main class for the flake8 extension."""

    # Plugin config
    name = PROJECT_NAME
    version = __version__

    # NitpickMixin
    error_class = InitError

    # Plugin arguments passed by Flake8
    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    def run(self) -> Iterator[Flake8Error]:
        """Run the check plugin."""
        for err in self.collect_nitpick_errors():
            yield err.as_flake8_warning()

    def collect_nitpick_errors(self) -> Iterator[NitpickError]:
        """Collect all possible Nitpick errors."""
        nit = Nitpick.singleton()

        current_python_file = Path(self.filename)
        try:
            if not nit.project:
                raise NoRootDirError

            main_python_file: Path = nit.project.find_main_python_file()
            if current_python_file.absolute() != main_python_file.absolute():
                # Only report warnings once, for the main Python file of this project.
                LOGGER.debug("Ignoring file: %s", self.filename)
                return []
        except (NoRootDirError, NoPythonFileError) as err:
            yield err
            return []
        LOGGER.debug("Nitpicking file: %s", self.filename)

        has_errors = False
        for style_err in nit.project.merge_styles(nit.offline):
            has_errors = True
            yield style_err
        if has_errors:
            return []

        yield from nit.check_present_absent()

        # Get all root keys from the merged style.
        for config_key, config_dict in nit.project.style_dict.items():
            # All except "nitpick" are file names.
            if config_key == PROJECT_NAME:
                continue

            # For each file name, find the plugin(s) that can handle the file.
            for plugin_instance in nit.project.plugin_manager.hook.can_handle(  # pylint: disable=no-member
                data=FileData.create(nit.project, config_key)
            ):
                yield from plugin_instance.process(config_dict)

        return []

    @staticmethod
    def add_options(option_manager: OptionManager):
        """Add the offline option."""
        option_manager.add_option(
            NitpickFlag.OFFLINE.as_flake8_flag(), action="store_true", help=NitpickFlag.OFFLINE.value
        )

    @staticmethod
    def parse_options(option_manager: OptionManager, options, args):  # pylint: disable=unused-argument
        """Create the Nitpick app, set logging from the verbose flags, set offline mode.

        This function is called only once by flake8, so it's a good place to create the app.
        """
        log_mapping = {1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(level=log_mapping.get(options.verbose, logging.WARNING))

        nit = Nitpick.singleton().init(offline=bool(options.nitpick_offline or NitpickFlag.OFFLINE.get_environ()))
        LOGGER.info("Offline mode: %s", nit.offline)
