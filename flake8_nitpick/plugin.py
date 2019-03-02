"""Plugin module."""
import itertools
import logging
from pathlib import Path

import attr

from flake8_nitpick import __version__
from flake8_nitpick.config import NitpickConfig
from flake8_nitpick.constants import NAME, ROOT_PYTHON_FILES
from flake8_nitpick.files.base import BaseFile
from flake8_nitpick.generic import get_subclasses
from flake8_nitpick.types import YieldFlake8Error
from flake8_nitpick.utils import NitpickMixin

LOG = logging.getLogger("flake8.nitpick")


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
        config = NitpickConfig().get_singleton()
        if not config.find_root_dir(self.filename):
            yield self.flake8_error(1, "No root dir found (is this a Python project?)")
            return

        if not config.find_main_python_file():
            yield self.flake8_error(
                2,
                "None of those Python files was found in the root dir"
                + f" {config.root_dir}: {', '.join(ROOT_PYTHON_FILES)}",
            )
            return

        current_python_file = Path(self.filename)
        if current_python_file.absolute() != config.main_python_file.absolute():
            # Only report warnings once, for the main Python file of this project.
            LOG.info("Ignoring file: %s", self.filename)
            return
        LOG.info("Nitpicking file: %s", self.filename)

        for error in itertools.chain(config.load_toml(), config.check_absent_files()):
            yield error

        for checker_class in get_subclasses(BaseFile):
            checker = checker_class()
            for error in checker.check_exists():
                yield error

        return []
