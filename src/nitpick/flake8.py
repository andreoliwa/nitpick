"""Flake8 plugin to check files."""
import itertools
import logging
from pathlib import Path
from typing import Iterator

import attr
from flake8.options.manager import OptionManager

from nitpick import __version__
from nitpick.app import create_app
from nitpick.cli import NitpickFlag
from nitpick.constants import PROJECT_NAME
from nitpick.exceptions import (
    AbsentFileError,
    InitError,
    NitpickError,
    NoPythonFileError,
    NoRootDirError,
    PresentFileError,
)
from nitpick.plugins.base import FilePathTags
from nitpick.typedefs import Flake8Error

LOGGER = logging.getLogger(__name__)


def check_files(present: bool) -> Iterator[NitpickError]:
    """Check files that should be present or absent."""
    key = "present" if present else "absent"
    message = "exist" if present else "be deleted"
    absent = not present
    app = create_app()
    for file_name, extra_message in app.config.nitpick_files_section.get(key, {}).items():
        file_path: Path = app.project_root / file_name
        exists = file_path.exists()
        if (present and exists) or (absent and not exists):
            continue

        full_message = f"File {file_name} should {message}"
        if extra_message:
            full_message += f": {extra_message}"
        error_class = PresentFileError if present else AbsentFileError
        yield error_class(full_message)


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
        app = create_app()

        current_python_file = Path(self.filename)
        try:
            if current_python_file.absolute() != app.main_python_file.absolute():
                # Only report warnings once, for the main Python file of this project.
                LOGGER.debug("Ignoring file: %s", self.filename)
                return []
        except (NoRootDirError, NoPythonFileError) as err:
            yield err
            return []
        LOGGER.debug("Nitpicking file: %s", self.filename)

        has_errors = False
        for style_err in app.config.merge_styles():
            has_errors = True
            yield style_err
        if has_errors:
            return []

        yield from itertools.chain(check_files(True), check_files(False))

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

    @staticmethod
    def add_options(option_manager: OptionManager):
        """Add the offline option."""
        option_manager.add_option(
            NitpickFlag.OFFLINE.as_flake8_flag(),
            action="store_true",
            # dest="offline",
            help=NitpickFlag.OFFLINE.value,
        )

    @staticmethod
    def parse_options(option_manager: OptionManager, options, args):  # pylint: disable=unused-argument
        """Create the Nitpick app, set logging from the verbose flags, set offline mode.

        This function is called only once by flake8, so it's a good place to create the app.
        """
        log_mapping = {1: logging.INFO, 2: logging.DEBUG}
        logging.basicConfig(level=log_mapping.get(options.verbose, logging.WARNING))

        app = create_app()
        app.offline = bool(options.nitpick_offline or NitpickFlag.OFFLINE.get_environ())
        LOGGER.info("Offline mode: %s", app.offline)
