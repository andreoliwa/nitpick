# -*- coding: utf-8 -*-
"""Flake8 plugin to check files."""
import itertools
import logging
from pathlib import Path

import attr

from nitpick import __version__
from nitpick.config import NitpickConfig
from nitpick.constants import LOG_ROOT, PROJECT_NAME, ROOT_PYTHON_FILES
from nitpick.files.base import BaseFile
from nitpick.generic import get_subclasses
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import YieldFlake8Error

LOGGER = logging.getLogger("{}.plugin".format(LOG_ROOT))


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
        self.config = NitpickConfig().get_singleton()
        if not self.config.find_root_dir(self.filename):
            yield self.flake8_error(1, "No root dir found (is this a Python project?)")
            return

        if not self.config.find_main_python_file():
            yield self.flake8_error(
                2,
                "None of those Python files was found in the root dir"
                + " {}: {}".format(self.config.root_dir, ", ".join(ROOT_PYTHON_FILES)),
            )
            return

        current_python_file = Path(self.filename)
        if current_python_file.absolute() != self.config.main_python_file.absolute():
            # Only report warnings once, for the main Python file of this project.
            LOGGER.info("Ignoring file: %s", self.filename)
            return
        LOGGER.info("Nitpicking file: %s", self.filename)

        yield from itertools.chain(self.config.merge_styles(), self.check_absent_files())

        for checker_class in get_subclasses(BaseFile):
            checker = checker_class()
            yield from checker.check_exists()

        return []

    def check_absent_files(self) -> YieldFlake8Error:
        """Check absent files."""
        for file_name, delete_message in self.config.files.get("absent", {}).items():
            file_path = self.config.root_dir / file_name  # type: Path
            if not file_path.exists():
                continue

            full_message = "File {} should be deleted".format(file_name)
            if delete_message:
                full_message += ": {}".format(delete_message)

            yield self.flake8_error(3, full_message)
