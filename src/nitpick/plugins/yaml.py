"""YAML files."""
from itertools import chain
from typing import Iterator, Optional, Type, cast

from nitpick.documents import BaseDoc, YamlDoc, traverse_yaml_tree
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.plugins.text import KEY_CONTAINS
from nitpick.typedefs import JsonDict, YamlObject
from nitpick.violations import Fuss, SharedViolations, ViolationEnum

KEY_REPOS = "repos"
KEY_YAML = "yaml"


class YamlPlugin(NitpickPlugin):
    """Enforce configurations and autofix YAML files."""

    identify_tags = {"yaml"}
    violation_base_code = 360
    fixable = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing data in the YAML file."""
        if KEY_CONTAINS in self.expected_config:
            # If the expected configuration has this key, it means that this config is being handled by TextPlugin.
            # TODO: A YAML file that has a "contains" key on its root cannot be handled as YAML... how to fix this?
            return

        yaml_doc = YamlDoc(path=self.file_path)
        comparison = yaml_doc.compare_with_flatten(self._remove_yaml_subkey(self.expected_config))
        if not comparison.has_changes:
            return

        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, yaml_doc.as_object, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, yaml_doc.as_object, comparison.missing, comparison.replace),
        )
        if self.autofix and self.dirty:
            yaml_doc.updater.dump(yaml_doc.as_object, self.file_path)

    @staticmethod
    def _remove_yaml_subkey(old_config: JsonDict) -> JsonDict:
        """Remove the obsolete "yaml" key that was used in the deprecated ``PreCommitPlugin``."""
        if KEY_REPOS not in old_config:
            return old_config
        new_config = old_config.copy()
        new_config[KEY_REPOS] = []
        for repo in old_config[KEY_REPOS]:  # type: JsonDict
            new_repo = repo.copy()
            new_repo.pop(KEY_YAML, None)
            if bool(new_repo):
                new_config[KEY_REPOS].append(new_repo)
        return new_config

    def report(
        self,
        violation: ViolationEnum,
        yaml_object: YamlObject,
        change: Optional[BaseDoc],
        replacement: Optional[BaseDoc] = None,
    ):
        """Report a violation while optionally modifying the YAML document."""
        if not (change or replacement):
            return
        if self.autofix:
            real_change = cast(BaseDoc, replacement or change)
            traverse_yaml_tree(yaml_object, real_change.as_object)
            self.dirty = True

        to_display = cast(BaseDoc, change or replacement)
        yield self.reporter.make_fuss(violation, to_display.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.write_initial_contents(YamlDoc)


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """Handle YAML files."""
    return YamlPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle YAML files."""
    if YamlPlugin.identify_tags & info.tags:
        return YamlPlugin
    return None
