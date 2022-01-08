"""YAML files."""
from collections import OrderedDict
from itertools import chain
from typing import Iterator, Optional, Tuple, Type, Union, cast

import attr

from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.documents import BaseDoc, YamlDoc, traverse_yaml_tree
from nitpick.exceptions import Deprecation
from nitpick.generic import jmes_search_json
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


@attr.s()
class PreCommitHook:
    """A pre-commit hook.

    .. note::

        This is a class from the deprecated ``nitpick.plugins.pre_commit.PreCommitPlugin``.
        It's not being used at the moment, but it was kept here because it's harmless.
    """

    repo = attr.ib(type=str)
    hook_id = attr.ib(type=str)
    yaml = attr.ib(type=YamlDoc)

    @property
    def unique_key(self) -> str:
        """Unique key of this hook, to be used in a dict."""
        return f"{self.repo}_{self.hook_id}"

    @property
    def key_value_pair(self) -> Tuple[str, "PreCommitHook"]:
        """Key/value pair to be used as a dict item."""
        return self.unique_key, self

    @property
    def single_hook(self) -> JsonDict:
        """Return only a single hook instead of a list."""
        return self.yaml.as_list[0]

    @classmethod
    def get_all_hooks_from(cls, str_or_yaml: Union[str, YamlObject]):
        """Get all hooks from a YAML string. Split the string in hooks and copy the repo info for each."""
        yaml = YamlDoc(string=str_or_yaml).as_list if isinstance(str_or_yaml, str) else str_or_yaml
        hooks = []
        for repo in yaml:
            for index, hook in enumerate(repo.get(KEY_HOOKS, [])):
                repo_data_only = repo.copy()
                repo_data_only.pop(KEY_HOOKS)
                hook_data_only = jmes_search_json(f"{KEY_HOOKS}[{index}]", repo, {})
                repo_data_only.update({KEY_HOOKS: [hook_data_only]})
                hooks.append(
                    PreCommitHook(repo.get(KEY_REPO), hook[KEY_ID], YamlDoc(obj=[repo_data_only])).key_value_pair  # type: ignore[arg-type]
                )
        return OrderedDict(hooks)


class YamlPlugin(NitpickPlugin):
    """Enforce configurations and autofix YAML files.

    - Example: `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_.
    - Style example: :ref:`the default pre-commit hooks <example-pre-commit-hooks>`.

    .. warning::

        The plugin tries to preserve comments in the YAML file by using the ``ruamel.yaml`` package.
        It works for most cases.
        If your comment was removed, place them in a different place of the fil and try again.
        If it still doesn't work, please `report a bug <https://github.com/andreoliwa/nitpick/issues/new/choose>`_.

    Known issue: lists like ``args`` and ``additional_dependencies`` might be joined in a single line,
        and comments between items will be removed.
    Move your comments outside these lists, and they should be preserved.

    .. note::

        No validation of ``.pre-commit-config.yaml`` will be done anymore in this generic YAML plugin.
        Nitpick_ will not validate hooks and missing keys as it did before; it's not the purpose of this package.
    """

    identify_tags = {"yaml"}
    violation_base_code = 360
    fixable = True

    @property
    def unique_keys_default(self) -> JsonDict:
        """Default unique keys for .pre-commit-config.yaml."""
        if self.filename == PRE_COMMIT_CONFIG_YAML:
            return {"repos": ["id", "hooks"]}
        return super().unique_keys_default

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing data in the YAML file."""
        if KEY_CONTAINS in self.expected_config:
            # If the expected configuration has this key, it means that this config is being handled by TextPlugin.
            # TODO: A YAML file that has a "contains" key on its root cannot be handled as YAML... how to fix this?
            return

        yaml_doc = YamlDoc(path=self.file_path)
        comparison = yaml_doc.compare_with_flatten(self._remove_yaml_subkey(self.expected_config), self.unique_keys)
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
        return self.write_initial_contents(YamlDoc, self._remove_yaml_subkey(self.expected_config))


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
