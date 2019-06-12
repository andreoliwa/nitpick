# -*- coding: utf-8 -*-
"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from collections import OrderedDict
from typing import Any, Dict, List, Tuple

import attr

from nitpick.files.base import BaseFile
from nitpick.formats import Yaml
from nitpick.generic import find_object_by_key
from nitpick.typedefs import YamlData, YieldFlake8Error

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
    yaml = attr.ib(type=Yaml)

    @property
    def unique_key(self) -> str:
        """Unique key of this hook, to be used in a dict."""
        return "{}_{}".format(self.repo, self.hook_id)

    @property
    def key_value_pair(self) -> Tuple[str, "PreCommitHook"]:
        """Key/value pair to be used as a dict item."""
        return self.unique_key, self

    @property
    def repo_short(self) -> str:
        """Short name of the repo."""
        return self.repo.split("/")[-1]

    @classmethod
    def get_all_hooks_from(cls, yaml: YamlData):
        """Get all hooks from a YAML string."""
        return OrderedDict(
            [
                PreCommitHook(repo.get(KEY_REPO), hook[KEY_ID], Yaml(data=repo)).key_value_pair
                for repo in yaml
                for hook in repo.get(KEY_HOOKS, [])
            ]
        )


class PreCommitFile(BaseFile):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""

    file_name = ".pre-commit-config.yaml"
    error_base_number = 330

    actual_yaml = None  # type: Yaml
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
                repo_list = Yaml(string=hooks_or_yaml).as_list
                suggested[KEY_REPOS].extend(repo_list)
            else:
                # TODO: show a deprecation warning for this case
                new_repo[KEY_HOOKS] = Yaml(string=hooks_or_yaml).as_data
                suggested[KEY_REPOS].append(new_repo)
        suggested.update(original)
        return Yaml(data=suggested).reformatted

    def check_rules(self) -> YieldFlake8Error:
        """Check the rules for the pre-commit hooks."""
        self.actual_yaml = Yaml(path=self.file_path)
        if KEY_REPOS not in self.actual_yaml.as_data:
            yield self.flake8_error(1, " doesn't have the {!r} root key".format(KEY_REPOS))
            return
        yield from self.check_root_values()
        yield from self.check_hooks()

    def check_root_values(self) -> YieldFlake8Error:
        """Check the root values in the configuration file."""
        actual = self.actual_yaml.as_data.copy()
        actual.pop(KEY_REPOS, None)

        expected = dict(self.file_dict).copy()
        expected.pop(KEY_REPOS, None)

        # FIXME: yield from self.check_missing_different(Comparison)
        # FIXME: Yaml(data=actual, ignore_keys=[KEY_REPOS])
        comparison = Yaml(data=actual).compare_with_dictdiffer(expected)
        if comparison.missing_format:
            yield self.flake8_error(8, " has missing values:\n{}".format(comparison.missing_format.reformatted))
        if comparison.diff_format:
            yield self.flake8_error(9, " has different values:\n{}".format(comparison.diff_format.reformatted))

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
        expected_hooks = PreCommitHook.get_all_hooks_from(Yaml(string=expected_repo_block.get(KEY_YAML)).as_list)
        for unique_key, hook in expected_hooks.items():
            if unique_key not in self.actual_hooks:
                yield self.flake8_error(
                    2,
                    ": repo {!r} not found. Use this:\n{}".format(
                        hook.repo_short, Yaml(data=[hook.yaml.as_data]).reformatted
                    ),
                )
                continue

            # FIXME: use jmespath to compare only hook data and not the full repo YAML
            # comparison = Yaml(data=self.actual_hooks[unique_key].yaml).compare_with_dictdiffer(hook.yaml)
            # if comparison.missing_format:
            #     yield self.flake8_error(
            #         3,
            #         ": repo {!r} has missing values. Use this:\n{}".format(
            #             full_name, comparison.missing_format.reformatted
            #         ),
            #     )
            # if comparison.diff_format:
            #     yield self.flake8_error(
            #         4,
            #         ": repo {!r} has different values. Use this:\n{}".format(
            #             full_name, comparison.diff_format.reformatted
            #         ),
            #     )

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

        expected_hooks = Yaml(string=yaml_expected_hooks).as_data
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
        lines = Yaml(data=expected_dict).reformatted
        output = []  # type: List[str]
        for line in lines.split("\n"):
            if line.startswith("id:"):
                output.insert(0, "  - {}".format(line))
            else:
                output.append("    {}".format(line))
        return "\n".join(output)
