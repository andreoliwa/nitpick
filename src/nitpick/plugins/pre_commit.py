"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from collections import OrderedDict
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, Union

import attr

from nitpick.exceptions import NitpickError
from nitpick.formats import YAMLFormat
from nitpick.generic import find_object_by_key, search_dict
from nitpick.plugins import hookimpl
from nitpick.plugins.base import FilePathTags, NitpickPlugin
from nitpick.typedefs import JsonDict, YamlData

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


class PreCommitError(NitpickError):
    """Base for pre-commit errors."""

    error_base_number = 330


class NoRootKeyError(PreCommitError):
    """No root key."""

    number = 1


class HookNotFoundError(PreCommitError):
    """Hook not found."""

    number = 2


class RepoDoesNotExistError(PreCommitError):
    """Repo does not exist."""

    number = 3


class MissingKeyInRepoError(PreCommitError):
    """Missing key in repo."""

    number = 4


class StyleFileMissingNameError(PreCommitError):
    """Missing name."""

    number = 5


class MissingKeyInHookError(PreCommitError):
    """Missing key in hook."""

    number = 6


class MissingHookWithIDError(PreCommitError):
    """Missing hook with specified ID."""

    number = 7


class PreCommitPlugin(NitpickPlugin):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file.

    Example: :ref:`the default pre-commit hooks <default-pre-commit-hooks>`.
    """

    file_name = ".pre-commit-config.yaml"
    error_class = PreCommitError

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

    def check_rules(self) -> Iterator[NitpickError]:
        """Check the rules for the pre-commit hooks."""
        self.actual_yaml = YAMLFormat(path=self.file_path)
        if KEY_REPOS not in self.actual_yaml.as_data:
            # TODO: if the 'repos' key doesn't exist, assume repos are in the root of the .yml file
            #  Having the 'repos' key is not actually a requirement. 'pre-commit-validate-config' works without it.
            yield NoRootKeyError(f" doesn't have the {KEY_REPOS!r} root key")
            return

        # Check the root values in the configuration file
        yield from self.warn_missing_different(
            YAMLFormat(data=self.actual_yaml.as_data, ignore_keys=[KEY_REPOS]).compare_with_dictdiffer(self.file_dict)
        )

        yield from self.check_hooks()

    def check_hooks(self) -> Iterator[NitpickError]:
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

    def check_repo_block(self, expected_repo_block: OrderedDict) -> Iterator[NitpickError]:
        """Check a repo with a YAML string configuration."""
        expected_hooks = PreCommitHook.get_all_hooks_from(YAMLFormat(string=expected_repo_block.get(KEY_YAML)).as_list)
        for unique_key, hook in expected_hooks.items():
            if unique_key not in self.actual_hooks:
                yield HookNotFoundError(
                    f": hook {hook.hook_id!r} not found. Use this:", YAMLFormat(data=hook.yaml.as_data).reformatted
                )
                continue

            comparison = YAMLFormat(data=self.actual_hooks[unique_key].single_hook).compare_with_dictdiffer(
                hook.single_hook
            )

            # Display the current revision of the hook
            current_revision = comparison.flat_actual.get("rev", None)
            revision_message = " (rev: {})".format(current_revision) if current_revision else ""
            yield from self.warn_missing_different(comparison, ": hook {!r}{}".format(hook.hook_id, revision_message))

    def check_repo_old_format(self, index: int, repo_data: OrderedDict) -> Iterator[NitpickError]:
        """Check repos using the old deprecated format with ``hooks`` and ``repo`` keys."""
        actual = self.actual_yaml.as_data.get(KEY_REPOS, [])  # type: List[YamlData]

        repo_name = repo_data.get(KEY_REPO)

        if not repo_name:
            yield HookNotFoundError(f": style file is missing {KEY_REPO!r} key in repo #{index}")
            return

        actual_repo_dict = find_object_by_key(actual, KEY_REPO, repo_name)
        if not actual_repo_dict:
            yield RepoDoesNotExistError(f": repo {repo_name!r} does not exist under {KEY_REPOS!r}")
            return

        if KEY_HOOKS not in actual_repo_dict:
            yield MissingKeyInRepoError(f": missing {KEY_HOOKS!r} in repo {repo_name!r}")
            return

        actual_hooks = actual_repo_dict.get(KEY_HOOKS) or []
        yaml_expected_hooks = repo_data.get(KEY_HOOKS)
        if not yaml_expected_hooks:
            yield StyleFileMissingNameError(f": style file is missing {KEY_HOOKS!r} in repo {repo_name!r}")
            return

        expected_hooks = YAMLFormat(string=yaml_expected_hooks).as_data
        for expected_dict in expected_hooks:
            hook_id = expected_dict.get(KEY_ID)
            if not hook_id:
                expected_yaml = self.format_hook(expected_dict)
                yield MissingKeyInHookError(f": style file is missing {KEY_ID!r} in hook:\n{expected_yaml}")
                continue
            actual_dict = find_object_by_key(actual_hooks, KEY_ID, hook_id)
            if not actual_dict:
                expected_yaml = self.format_hook(expected_dict)
                yield MissingHookWithIDError(f": missing hook with id {hook_id!r}:\n{expected_yaml}")
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
def can_handle(file: FilePathTags) -> Optional["NitpickPlugin"]:  # pylint: disable=unused-argument
    """Handle pre-commit config file."""
    if file.path_from_root == PreCommitPlugin.file_name:
        return PreCommitPlugin()
    return None
