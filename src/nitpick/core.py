"""The Nitpick application."""
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import Iterator, Union

from loguru import logger

from nitpick import PROJECT_NAME
from nitpick.exceptions import FileShouldBeDeletedError, MissingFileError, NitpickError
from nitpick.plugins.base import FileData
from nitpick.project import Project


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

    def init(self, path_or_project: Union[Path, Project] = None, offline: bool = None) -> "Nitpick":
        """Initialize attributes of the singleton."""
        if path_or_project is None or isinstance(path_or_project, (Path, str)):
            self.project = Project(path_or_project)
        elif isinstance(path_or_project, Project):
            self.project = path_or_project
        else:
            raise TypeError("path_or_project should be a Path or a Project")

        if offline is not None:
            self.offline = offline

        return self

    def run(self) -> Iterator[NitpickError]:
        """Run Nitpick."""
        yield from chain(self.project.merge_styles(self.offline), self.enforce_present_absent(), self.enforce_style())

    def enforce_present_absent(self) -> Iterator[NitpickError]:
        """Enforce files that should be present or absent."""
        if not self.project:
            return

        for present in (True, False):
            key = "present" if present else "absent"
            logger.info(f"Enforce {key} files")
            message = "exist" if present else "be deleted"
            absent = not present
            for file_name, extra_message in self.project.nitpick_files_section.get(key, {}).items():
                file_path: Path = self.project.root / file_name
                exists = file_path.exists()
                if (present and exists) or (absent and not exists):
                    continue

                full_message = f"File {file_name} should {message}"
                if extra_message:
                    full_message += f": {extra_message}"
                error_class = MissingFileError if present else FileShouldBeDeletedError
                yield error_class(full_message)

    def enforce_style(self):
        """Read the merged style and enforce the rules in it.

        1. Get all root keys from the merged style
        2. All except "nitpick" are file names.
        3. For each file name, find the plugin(s) that can handle the file.
        """

        # 1.
        for config_key, config_dict in self.project.style_dict.items():
            logger.info(f"{config_key}: Finding plugins to enforce style")

            # 2.
            if config_key == PROJECT_NAME:
                continue

            # 3.
            for plugin_instance in self.project.plugin_manager.hook.can_handle(  # pylint: disable=no-member
                data=FileData.create(self.project, config_key)
            ):
                yield from plugin_instance.entry_point(config_dict)
