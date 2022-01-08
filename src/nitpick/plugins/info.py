"""Info needed by the plugins."""
from dataclasses import dataclass, field
from typing import Set

from identify import identify

from nitpick.constants import DOT
from nitpick.exceptions import Deprecation
from nitpick.project import Project


@dataclass
class FileInfo:
    """File information needed by the plugin."""

    project: Project
    path_from_root: str
    tags: Set[str] = field(default_factory=set)

    @classmethod
    def create(cls, project: Project, path_from_root: str) -> "FileInfo":
        """Clean the file name and get its tags."""
        if Deprecation.pre_commit_without_dash(path_from_root):
            clean_path = DOT + path_from_root
        else:
            clean_path = DOT + path_from_root[1:] if path_from_root.startswith("-") else path_from_root
        tags = set(identify.tags_from_filename(clean_path))
        return cls(project, clean_path, tags)
