"""Flake8 plugin to check files."""
import itertools
import logging
from pathlib import Path

import attr

from nitpick import Nitpick, __version__
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
            LOGGER.info("Ignoring file: %s", self.filename)
            return []
        LOGGER.info("Nitpicking file: %s", self.filename)

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
