"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

import attr

from nitpick.formats import TOMLFormat, YAMLFormat
from nitpick.generic import find_object_by_key, search_dict
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.typedefs import JsonDict, YamlData, YieldFlake8Error

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
        return "{}_{}".format(self.repo, self.hook_id)

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
                hook_data_only = search_dict("{}[{}]".format(KEY_HOOKS, index), repo, {})
                repo_data_only.update({KEY_HOOKS: [hook_data_only]})
                hooks.append(
                    PreCommitHook(repo.get(KEY_REPO), hook[KEY_ID], YAMLFormat(data=[repo_data_only])).key_value_pair
                )
        return OrderedDict(hooks)


class PreCommitPlugin(NitpickPlugin):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file.

    Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.
    """

    file_name = ".pre-commit-config.yaml"
    error_base_number = 330

    actual_yaml = None  # type: YAMLFormat
    actual_hooks = OrderedDict()  # type: OrderedDict[str, PreCommitHook]
    actual_hooks_by_key = {}  # type: Dict[str, int]
    actual_hooks_by_index = []  # type: List[str]

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        original = dict(self.file_dict).copy()
        original_repos = original.pop(KEY_REPOS, [])
        suggested = {KEY_REPOS: []} if original_repos else {}  # type: Dict[str, Any]
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

    def check_rules(self) -> YieldFlake8Error:
        """Check the rules for the pre-commit hooks."""
        self.actual_yaml = YAMLFormat(path=self.file_path)
        if KEY_REPOS not in self.actual_yaml.as_data:
            # TODO: if the 'repos' key doesn't exist, assume repos are in the root of the .yml file
            #  Having the 'repos' key is not actually a requirement. 'pre-commit-validate-config' works without it.
            yield self.flake8_error(1, " doesn't have the {!r} root key".format(KEY_REPOS))
            return

        # Check the root values in the configuration file
        yield from self.warn_missing_different(
            YAMLFormat(data=self.actual_yaml.as_data, ignore_keys=[KEY_REPOS]).compare_with_dictdiffer(self.file_dict)
        )

        yield from self.check_hooks()

    def check_hooks(self) -> YieldFlake8Error:
        """Check the repositories configured in pre-commit."""
        self.actual_hooks = PreCommitHook.get_all_hooks_from(self.actual_yaml.as_data.get(KEY_REPOS))
        self.actual_hooks_by_key = {name: index for index, name in enumerate(self.actual_hooks)}
        self.actual_hooks_by_index = list(self.actual_hooks)

        all_expected_blocks = self.file_dict.get(KEY_REPOS, [])  # type: List[OrderedDict]
        for index, data in enumerate(all_expected_blocks):
            if KEY_YAML in data:
                yield from self.check_repo_block(data)
                continue

            yield from self.check_repo_old_format(index, data)

    def check_repo_block(self, expected_repo_block: OrderedDict) -> YieldFlake8Error:
        """Check a repo with a YAML string configuration."""
        expected_hooks = PreCommitHook.get_all_hooks_from(YAMLFormat(string=expected_repo_block.get(KEY_YAML)).as_list)
        for unique_key, hook in expected_hooks.items():
            if unique_key not in self.actual_hooks:
                yield self.flake8_error(
                    2,
                    ": hook {!r} not found. Use this:".format(hook.hook_id),
                    YAMLFormat(data=hook.yaml.as_data).reformatted,
                )
                continue

            comparison = YAMLFormat(data=self.actual_hooks[unique_key].single_hook).compare_with_dictdiffer(
                hook.single_hook
            )

            # Display the current revision of the hook
            current_revision = comparison.flat_actual.get("rev", None)
            revision_message = " (rev: {})".format(current_revision) if current_revision else ""
            yield from self.warn_missing_different(comparison, ": hook {!r}{}".format(hook.hook_id, revision_message))

    def check_repo_old_format(self, index: int, repo_data: OrderedDict) -> YieldFlake8Error:
        """Check repos using the old deprecated format with ``hooks`` and ``repo`` keys."""
        actual = self.actual_yaml.as_data.get(KEY_REPOS, [])  # type: List[YamlData]

        repo_name = repo_data.get(KEY_REPO)
        if not repo_name:
            yield self.flake8_error(2, ": style file is missing {!r} key in repo #{}".format(KEY_REPO, index))
            return

        actual_repo_dict = find_object_by_key(actual, KEY_REPO, repo_name)
        if not actual_repo_dict:
            yield self.flake8_error(3, ": repo {!r} does not exist under {!r}".format(repo_name, KEY_REPOS))
            return

        if KEY_HOOKS not in actual_repo_dict:
            yield self.flake8_error(4, ": missing {!r} in repo {!r}".format(KEY_HOOKS, repo_name))
            return

        actual_hooks = actual_repo_dict.get(KEY_HOOKS) or []
        yaml_expected_hooks = repo_data.get(KEY_HOOKS)
        if not yaml_expected_hooks:
            yield self.flake8_error(5, ": style file is missing {!r} in repo {!r}".format(KEY_HOOKS, repo_name))
            return

        expected_hooks = YAMLFormat(string=yaml_expected_hooks).as_data
        for expected_dict in expected_hooks:
            hook_id = expected_dict.get(KEY_ID)
            if not hook_id:
                expected_yaml = self.format_hook(expected_dict)
                yield self.flake8_error(6, ": style file is missing {!r} in hook:\n{}".format(KEY_ID, expected_yaml))
                continue
            actual_dict = find_object_by_key(actual_hooks, KEY_ID, hook_id)
            if not actual_dict:
                expected_yaml = self.format_hook(expected_dict)
                yield self.flake8_error(7, ": missing hook with id {!r}:\n{}".format(hook_id, expected_yaml))
                continue

    @staticmethod
    def format_hook(expected_dict) -> str:
        """Format the hook so it's easy to copy and paste it to the .yaml file: ID goes first, indent with spaces."""
        lines = YAMLFormat(data=expected_dict).reformatted
        output = []  # type: List[str]
        for line in lines.split("\n"):
            if line.startswith("id:"):
                output.insert(0, "  - {}".format(line))
            else:
                output.append("    {}".format(line))
        return "\n".join(output)


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return PreCommitPlugin


@hookimpl
def handle_config_file(  # pylint: disable=unused-argument
    config: JsonDict, file_name: str, tags: Set[str]
) -> Optional["NitpickPlugin"]:
    """Handle pre-commit config file."""
    return PreCommitPlugin(config) if file_name == TOMLFormat.group_name_for(PreCommitPlugin.file_name) else None
