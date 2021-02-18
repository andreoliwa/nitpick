"""The Nitpick application."""
import os
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List

import click
from loguru import logger

from nitpick.constants import PROJECT_NAME
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import relative_to_current_dir
from nitpick.plugins.data import FileData
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

    def run(self, *partial_names: str, check=True) -> Iterator[Fuss]:
        """Run Nitpick."""
        Reporter.reset()

        try:
            yield from chain(
                self.project.merge_styles(self.offline),
                self.enforce_present_absent(),
                self.enforce_style(*partial_names, check=check),
            )
        except QuitComplainingError as err:
            yield from err.violations

    def enforce_present_absent(self) -> Iterator[Fuss]:
        """Enforce files that should be present or absent."""
        if not self.project:
            return

        for present in (True, False):
            key = "present" if present else "absent"
            logger.info(f"Enforce {key} files")
            absent = not present
            for filename, custom_message in self.project.nitpick_files_section.get(key, {}).items():
                file_path: Path = self.project.root / filename
                exists = file_path.exists()
                if (present and exists) or (absent and not exists):
                    continue

                reporter = Reporter(FileData.create(self.project, filename))

                extra = f": {custom_message}" if custom_message else ""
                violation = ProjectViolations.MissingFile if present else ProjectViolations.FileShouldBeDeleted
                yield reporter.make_fuss(violation, extra=extra)

    def enforce_style(self, *partial_names: str, check=False):
        """Read the merged style and enforce the rules in it.

        1. Get all root keys from the merged style
        2. All except "nitpick" are file names.
        3. For each file name, find the plugin(s) that can handle the file.
        """

        # 1.
        for config_key in self.filter_keys(*partial_names):
            config_dict = self.project.style_dict[config_key]
            logger.info(f"{config_key}: Finding plugins to enforce style")

            # 2.
            if config_key == PROJECT_NAME:
                continue

            # 3.
            for plugin_instance in self.project.plugin_manager.hook.can_handle(  # pylint: disable=no-member
                data=FileData.create(self.project, config_key)
            ):  # type: NitpickPlugin
                yield from plugin_instance.entry_point(config_dict, check)

    def filter_keys(self, *partial_names: str) -> List[str]:
        """Filter keys, keeping only the selected partial names."""
        rv = []
        for key in self.project.style_dict:
            if key == PROJECT_NAME:
                continue

            include = bool(not partial_names)
            for name in partial_names:
                if name in key:
                    include = True
                    break

            if include:
                rv.append(key)
        return rv

    def configured_files(self, *partial_names: str) -> List[Path]:
        """List of files configured in the Nitpick style. Filter only the selected partial names."""
        return [Path(self.project.root) / key for key in self.filter_keys(*partial_names)]

    def echo(self, message: str):
        """Echo a message on the terminal, with the relative path at the beginning."""
        relative = relative_to_current_dir(self.project.root)
        if relative:
            relative += os.path.sep
        click.echo(f"{relative}{message}")
