"""Enforce configuration for `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_."""
from collections import OrderedDict
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, Union

import attr

from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.formats import YAMLFormat
from nitpick.generic import find_object_by_key, search_dict
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.typedefs import JsonDict, YamlData
from nitpick.violations import Fuss, ViolationEnum

KEY_REPOS = "repos"
KEY_HOOKS = "hooks"
KEY_REPO = "repo"
KEY_ID = "id"
KEY_YAML = "yaml"


@attr.s()
class PreCommitHook:
    """A pre-commit hook."""

    repo = attr.ib(type=str)
    hook_id = attr.ib(type=str)
    yaml = attr.ib(type=YAMLFormat)

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
    def get_all_hooks_from(cls, str_or_yaml: Union[str, YamlData]):
        """Get all hooks from a YAML string. Split the string in hooks and copy the repo info for each."""
        yaml = YAMLFormat(string=str_or_yaml).as_list if isinstance(str_or_yaml, str) else str_or_yaml
        hooks = []
        for repo in yaml:
            for index, hook in enumerate(repo.get(KEY_HOOKS, [])):
                repo_data_only = repo.copy()
                repo_data_only.pop(KEY_HOOKS)
                hook_data_only = search_dict(f"{KEY_HOOKS}[{index}]", repo, {})
                repo_data_only.update({KEY_HOOKS: [hook_data_only]})
                hooks.append(
                    PreCommitHook(repo.get(KEY_REPO), hook[KEY_ID], YAMLFormat(data=[repo_data_only])).key_value_pair
                )
        return OrderedDict(hooks)


class Violations(ViolationEnum):
    """Violations for this plugin."""

    NO_ROOT_KEY = (331, f" doesn't have the {KEY_REPOS!r} root key")
    HOOK_NOT_FOUND = (332, ": hook {id!r} not found. Use this:")
    STYLE_MISSING_INDEX = (332, ": style file is missing {key!r} key in repo #{index}")
    REPO_DOES_NOT_EXIST = (333, ": repo {repo!r} does not exist under {key!r}")
    MISSING_KEY_IN_REPO = (334, ": missing {key!r} in repo {repo!r}")
    STYLE_FILE_MISSING_NAME = (335, ": style file is missing {key!r} in repo {repo!r}")
    MISSING_KEY_IN_HOOK = (336, ": style file is missing {key!r} in hook:\n{yaml}")
    MISSING_HOOK_WITH_ID = (337, ": missing hook with id {id!r}:\n{yaml}")


class PreCommitPlugin(NitpickPlugin):
    """Enforce configuration for `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_.

    Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.
    """

    filename = PRE_COMMIT_CONFIG_YAML
    violation_base_code = 330

    actual_yaml: YAMLFormat
    actual_hooks: Dict[str, PreCommitHook] = OrderedDict()
    actual_hooks_by_key: Dict[str, int] = {}
    actual_hooks_by_index: List[str] = []

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        original = dict(self.expected_config).copy()
        original_repos = original.pop(KEY_REPOS, [])
        suggested: Dict[str, Any] = {KEY_REPOS: []} if original_repos else {}
        for repo in original_repos:
            new_repo = dict(repo)
            hooks_or_yaml = repo.get(KEY_HOOKS, repo.get(KEY_YAML, {}))
            if KEY_YAML in repo:
                repo_list = YAMLFormat(string=hooks_or_yaml).as_list
                suggested[KEY_REPOS].extend(repo_list)
            else:
                # TODO: show a deprecation warning for this case
                new_repo[KEY_HOOKS] = YAMLFormat(string=hooks_or_yaml).as_data
                suggested[KEY_REPOS].append(new_repo)
        suggested.update(original)
        return YAMLFormat(data=suggested).reformatted

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for the pre-commit hooks."""
        self.actual_yaml = YAMLFormat(path=self.file_path)
        if KEY_REPOS not in self.actual_yaml.as_data:
            # TODO: if the 'repos' key doesn't exist, assume repos are in the root of the .yml file
            #  Having the 'repos' key is not actually a requirement. 'pre-commit-validate-config' works without it.
            yield self.reporter.make_fuss(Violations.NO_ROOT_KEY)
            return

        # Check the root values in the configuration file
        yield from self.warn_missing_different(
            YAMLFormat(data=self.actual_yaml.as_data, ignore_keys=[KEY_REPOS]).compare_with_dictdiffer(
                self.expected_config
            )
        )

        yield from self.enforce_hooks()

    def enforce_hooks(self) -> Iterator[Fuss]:
        """Enforce the repositories configured in pre-commit."""
        self.actual_hooks = PreCommitHook.get_all_hooks_from(self.actual_yaml.as_data.get(KEY_REPOS))
        self.actual_hooks_by_key = {name: index for index, name in enumerate(self.actual_hooks)}
        self.actual_hooks_by_index = list(self.actual_hooks)

        all_expected_blocks: List[OrderedDict] = self.expected_config.get(KEY_REPOS, [])
        for index, data in enumerate(all_expected_blocks):
            if KEY_YAML in data:
                yield from self.enforce_repo_block(data)
                continue

            yield from self.enforce_repo_old_format(index, data)

    def enforce_repo_block(self, expected_repo_block: OrderedDict) -> Iterator[Fuss]:
        """Enforce a repo with a YAML string configuration."""
        expected_hooks = PreCommitHook.get_all_hooks_from(YAMLFormat(string=expected_repo_block.get(KEY_YAML)).as_list)
        for unique_key, hook in expected_hooks.items():
            if unique_key not in self.actual_hooks:
                yield self.reporter.make_fuss(
                    Violations.HOOK_NOT_FOUND, YAMLFormat(data=hook.yaml.as_data).reformatted, id=hook.hook_id
                )
                continue

            comparison = YAMLFormat(data=self.actual_hooks[unique_key].single_hook).compare_with_dictdiffer(
                hook.single_hook
            )

            # Display the current revision of the hook
            current_revision = comparison.flat_actual.get("rev", None)
            revision_message = f" (rev: {current_revision})" if current_revision else ""
            yield from self.warn_missing_different(comparison, f": hook {hook.hook_id!r}{revision_message}")

    def enforce_repo_old_format(self, index: int, repo_data: OrderedDict) -> Iterator[Fuss]:
        """Enforce repos using the old deprecated format with ``hooks`` and ``repo`` keys."""
        actual: List[YamlData] = self.actual_yaml.as_data.get(KEY_REPOS, [])

        repo_name = repo_data.get(KEY_REPO)

        if not repo_name:
            yield self.reporter.make_fuss(Violations.STYLE_MISSING_INDEX, key=KEY_REPO, index=index)
            return

        actual_repo_dict = find_object_by_key(actual, KEY_REPO, repo_name)
        if not actual_repo_dict:
            yield self.reporter.make_fuss(Violations.REPO_DOES_NOT_EXIST, repo=repo_name, key=KEY_REPOS)
            return

        if KEY_HOOKS not in actual_repo_dict:
            yield self.reporter.make_fuss(Violations.MISSING_KEY_IN_REPO, key=KEY_HOOKS, repo=repo_name)
            return

        actual_hooks = actual_repo_dict.get(KEY_HOOKS) or []
        yaml_expected_hooks = repo_data.get(KEY_HOOKS)
        if not yaml_expected_hooks:
            yield self.reporter.make_fuss(Violations.STYLE_FILE_MISSING_NAME, key=KEY_HOOKS, repo=repo_name)
            return

        expected_hooks = YAMLFormat(string=yaml_expected_hooks).as_data
        for expected_dict in expected_hooks:
            hook_id = expected_dict.get(KEY_ID)
            expected_yaml = self.format_hook(expected_dict).rstrip()
            if not hook_id:
                yield self.reporter.make_fuss(Violations.MISSING_KEY_IN_HOOK, key=KEY_ID, yaml=expected_yaml)
                continue

            actual_dict = find_object_by_key(actual_hooks, KEY_ID, hook_id)
            if not actual_dict:
                yield self.reporter.make_fuss(Violations.MISSING_HOOK_WITH_ID, id=hook_id, yaml=expected_yaml)
                continue

    @staticmethod
    def format_hook(expected_dict) -> str:
        """Format the hook so it's easy to copy and paste it to the .yaml file: ID goes first, indent with spaces."""
        lines = YAMLFormat(data=expected_dict).reformatted
        output: List[str] = []
        for line in lines.split("\n"):
            if line.startswith("id:"):
                output.insert(0, f"  - {line}")
            else:
                output.append(f"    {line}")
        return "\n".join(output)


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return PreCommitPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle pre-commit config file."""
    if info.path_from_root == PRE_COMMIT_CONFIG_YAML:
        return PreCommitPlugin
    return None
