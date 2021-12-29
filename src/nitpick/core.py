"""The Nitpick application."""
import os
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Type

import click
from loguru import logger

from nitpick.exceptions import QuitComplainingError
from nitpick.generic import filter_names, relative_to_current_dir
from nitpick.plugins.info import FileInfo
from nitpick.project import Project
from nitpick.typedefs import PathOrStr
from nitpick.violations import Fuss, ProjectViolations, Reporter

if TYPE_CHECKING:
    from nitpick.plugins import NitpickPlugin


class Nitpick:
    """The Nitpick API."""

    _allow_init = False

    project: Project

    def __init__(self):
        if not self._allow_init:
            raise TypeError("This class cannot be instantiated directly. Use Nitpick.singleton().init(...) instead")

        self.offline: bool = False

    @classmethod
    @lru_cache()
    def singleton(cls) -> "Nitpick":
        """Return a single instance of the class."""
        Nitpick._allow_init = True
        instance = cls()
        Nitpick._allow_init = False
        return instance

    def init(self, project_root: PathOrStr = None, offline: bool = None) -> "Nitpick":
        """Initialize attributes of the singleton."""
        self.project = Project(project_root)

        if offline is not None:
            self.offline = offline

        return self

    def run(self, *partial_names: str, autofix=False) -> Iterator[Fuss]:
        """Run Nitpick.

        :param partial_names: Names of the files to enforce configs for.
        :param autofix: Flag to modify files, if the plugin supports it (default: True).
        :return: Fuss generator.
        """
        Reporter.reset()

        try:
            yield from chain(
                self.project.merge_styles(self.offline),
                self.enforce_present_absent(*partial_names),
                self.enforce_style(*partial_names, autofix=autofix),
            )
        except QuitComplainingError as err:
            yield from err.violations

    def enforce_present_absent(self, *partial_names: str) -> Iterator[Fuss]:
        """Enforce files that should be present or absent.

        :param partial_names: Names of the files to enforce configs for.
        :return: Fuss generator.
        """
        if not self.project:
            return

        for present in (True, False):
            key = "present" if present else "absent"
            logger.debug(f"Enforce {key} files")
            absent = not present
            file_mapping = self.project.nitpick_files_section.get(key, {})
            for filename in filter_names(file_mapping, *partial_names):
                custom_message = file_mapping[filename]
                file_path: Path = self.project.root / filename
                exists = file_path.exists()
                if (present and exists) or (absent and not exists):
                    continue

                reporter = Reporter(FileInfo.create(self.project, filename))

                extra = f": {custom_message}" if custom_message else ""
                violation = ProjectViolations.MISSING_FILE if present else ProjectViolations.FILE_SHOULD_BE_DELETED
                yield reporter.make_fuss(violation, extra=extra)

    def enforce_style(self, *partial_names: str, autofix=True) -> Iterator[Fuss]:
        """Read the merged style and enforce the rules in it.

        1. Get all root keys from the merged style (every key is a filename, except "nitpick").
        2. For each file name, find the plugin(s) that can handle the file.

        :param partial_names: Names of the files to enforce configs for.
        :param autofix: Flag to modify files, if the plugin supports it (default: True).
        :return: Fuss generator.
        """

        # 1.
        for config_key in filter_names(self.project.style_dict, *partial_names):
            config_dict = self.project.style_dict[config_key]
            logger.debug(f"{config_key}: Finding plugins to enforce style")

            # 2.
            info = FileInfo.create(self.project, config_key)
            # pylint: disable=no-member
            for plugin_class in self.project.plugin_manager.hook.can_handle(info=info):  # type: Type[NitpickPlugin]
                yield from plugin_class(info, config_dict, autofix).entry_point()

    def configured_files(self, *partial_names: str) -> List[Path]:
        """List of files configured in the Nitpick style. Filter only the selected partial names."""
        return [Path(self.project.root) / key for key in filter_names(self.project.style_dict, *partial_names)]

    def echo(self, message: str):
        """Echo a message on the terminal, with the relative path at the beginning."""
        relative = relative_to_current_dir(self.project.root)
        if relative:
            relative += os.path.sep
        click.echo(f"{relative}{message}")
