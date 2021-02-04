"""Flake8 plugin to check files."""
import logging
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import Iterator, Union

import attr
from flake8.options.manager import OptionManager
from loguru import logger

from nitpick import __version__
from nitpick.cli import NitpickFlag
from nitpick.constants import FLAKE8_PREFIX, PROJECT_NAME
from nitpick.core import Nitpick
from nitpick.exceptions import Fuss, InitError, NitpickError, NoPythonFileError, NoRootDirError
from nitpick.typedefs import Flake8Error


@attr.s(hash=False)
class NitpickFlake8Extension:
    """Main class for the flake8 extension."""

    # Plugin config
    name = PROJECT_NAME
    version = __version__

    # NitpickMixin
    error_class = InitError
    # FIXME[AA]: reporter = Reporter(100, InitCodes: CodeEnum)
    # FIXME[AA]: the Reporter class should track a global list of codes with __new__(),
    #  to be used by the `nitpick codes` CLI command

    # Plugin arguments passed by Flake8
    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    def run(self) -> Iterator[Flake8Error]:
        """Run the check plugin."""
        for err in self.collect_errors():
            yield self.build_flake8_error(err)

    def build_flake8_error(self, obj: Union[Fuss, NitpickError]) -> Flake8Error:
        """Return a flake8 error from objects."""
        if isinstance(obj, Fuss):
            line = f"{FLAKE8_PREFIX}{obj.code:03} {obj.message}{obj.suggestion}"
        elif isinstance(obj, NitpickError):
            line = f"{FLAKE8_PREFIX}{obj.error_code:03} {obj.error_prefix}{obj.message.rstrip()}{obj.suggestion_nl}"
        else:
            line = ""
        return (
            0,
            0,
            line,
            self.__class__,
        )

    def collect_errors(self) -> Iterator[NitpickError]:
        """Collect all possible Nitpick errors."""
        nit = Nitpick.singleton()

        current_python_file = Path(self.filename)
        try:
            if not nit.project:
                raise NoRootDirError

            main_python_file: Path = nit.project.find_main_python_file()
            if current_python_file.absolute() != main_python_file.absolute():
                # Only report warnings once, for the main Python file of this project.
                logger.debug("Ignoring file: {}", self.filename)
                return []
        except (NoRootDirError, NoPythonFileError) as err:
            # FIXME[AA]: a NitpickError can have List[Fuss]; collect all fusses,
            #  then raise an error with them to interrupt execution and return
            yield err  # make_error(no root/no python error??) or yield err.as_fuss
            return []
        logger.debug("Nitpicking file: {}", self.filename)

        has_errors = False
        for style_err in nit.project.merge_styles(nit.offline):
            has_errors = True
            # FIXME[AA]: a NitpickError can have List[Fuss]; collect all fusses,
            #  then raise an error with them to interrupt execution and return
            yield style_err  # make_error(style error??) or yield err.as_fuss
        if has_errors:
            return []

        yield from chain(nit.enforce_present_absent(), nit.enforce_style())
        return []

    @staticmethod
    @lru_cache()  # To avoid calling this function twice in the same process
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
        logger.info("Offline mode: {}", nit.offline)
