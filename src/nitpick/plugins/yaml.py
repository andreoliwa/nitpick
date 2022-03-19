"""YAML files."""
from __future__ import annotations

from itertools import chain
from typing import Iterator, cast

from nitpick.blender import Comparison, YamlDoc, traverse_yaml_tree
from nitpick.config import SpecialConfig
from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.exceptions import Deprecation
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.plugins.text import KEY_CONTAINS
from nitpick.typedefs import JsonDict, YamlObject
from nitpick.violations import Fuss, SharedViolations, ViolationEnum

KEY_REPOS = "repos"
KEY_YAML = "yaml"
KEY_HOOKS = "hooks"
KEY_REPO = "repo"
KEY_ID = "id"


class YamlPlugin(NitpickPlugin):
    """Enforce configurations and autofix YAML files.

    - Example: `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_.
    - Style example: :gitref:`the default pre-commit hooks <src/nitpick/resources/any/pre-commit-hooks.toml>`.

    .. warning::

        The plugin tries to preserve comments in the YAML file by using the ``ruamel.yaml`` package.
        It works for most cases.
        If your comment was removed, place them in a different place of the fil and try again.
        If it still doesn't work, please :issue:`report a bug <new/choose>`.

    Known issue: lists like ``args`` and ``additional_dependencies`` might be joined in a single line,
    and comments between items will be removed.
    Move your comments outside these lists, and they should be preserved.

    .. note::

        No validation of ``.pre-commit-config.yaml`` will be done anymore in this generic YAML plugin.
        Nitpick will not validate hooks and missing keys as it did before; it's not the purpose of this package.
    """

    identify_tags = {"yaml"}
    violation_base_code = 360
    fixable = True

    def predefined_special_config(self) -> SpecialConfig:
        """Predefined special config, with list keys for .pre-commit-config.yaml and GitHub Workflow files."""
        spc = SpecialConfig()
        # pylint: disable=assigning-non-slot
        if self.filename == PRE_COMMIT_CONFIG_YAML:
            spc.list_keys.from_plugin = {"repos": "hooks.id"}
        elif self.filename.startswith(".github/workflows"):
            spc.list_keys.from_plugin = {"jobs.*.steps": "name"}
        return spc

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing data in the YAML file."""
        if KEY_CONTAINS in self.expected_config:
            # If the expected configuration has this key, it means that this config is being handled by TextPlugin.
            # TODO: fix: allow a YAML file with a "contains" key on its root (how?)
            return

        yaml_doc = YamlDoc(path=self.file_path)
        comparison = Comparison(yaml_doc, self._remove_yaml_subkey(self.expected_config), self.special_config)()
        if not comparison.has_changes:
            return

        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, yaml_doc.as_object, cast(YamlDoc, comparison.diff)),
            self.report(
                SharedViolations.MISSING_VALUES,
                yaml_doc.as_object,
                cast(YamlDoc, comparison.missing),
                cast(YamlDoc, comparison.replace),
            ),
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
        repos_with_yaml_key = False
        for repo in old_config[KEY_REPOS]:  # type: JsonDict
            new_repo = repo.copy()
            if KEY_YAML in new_repo:
                new_repo.pop(KEY_YAML, None)
                repos_with_yaml_key = True
            if bool(new_repo):
                new_config[KEY_REPOS].append(new_repo)

        if repos_with_yaml_key:
            Deprecation.pre_commit_repos_with_yaml_key()

        return new_config

    def report(
        self,
        violation: ViolationEnum,
        yaml_object: YamlObject,
        change: YamlDoc | None,
        replacement: YamlDoc | None = None,
    ):
        """Report a violation while optionally modifying the YAML document."""
        if not (change or replacement):
            return
        if self.autofix:
            real_change = cast(YamlDoc, replacement or change)
            traverse_yaml_tree(yaml_object, real_change.as_object)
            self.dirty = True

        to_display = cast(YamlDoc, change or replacement)
        yield self.reporter.make_fuss(violation, to_display.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.write_initial_contents(YamlDoc, self._remove_yaml_subkey(self.expected_config))


@hookimpl
def plugin_class() -> type[NitpickPlugin]:
    """Handle YAML files."""
    return YamlPlugin


@hookimpl
def can_handle(info: FileInfo) -> type[NitpickPlugin] | None:
    """Handle YAML files."""
    if YamlPlugin.identify_tags & info.tags:
        return YamlPlugin
    return None
