# -*- coding: utf-8 -*-
"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from collections import OrderedDict
from typing import Any, Dict, List

from nitpick.files.base import BaseFile
from nitpick.formats import Yaml
from nitpick.generic import find_object_by_key
from nitpick.typedefs import YamlData, YieldFlake8Error


class PreCommitFile(BaseFile):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""

    file_name = ".pre-commit-config.yaml"
    error_base_number = 330
    actual_yaml = None  # type: Yaml

    KEY_REPOS = "repos"
    KEY_HOOKS = "hooks"
    KEY_REPO = "repo"
    KEY_ID = "id"
    KEY_YAML = "yaml"

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        original = dict(self.file_dict).copy()
        original_repos = original.pop(self.KEY_REPOS, [])
        suggested = {self.KEY_REPOS: []} if original_repos else {}  # type: Dict[str, Any]
        for repo in original_repos:
            new_repo = dict(repo)
            hooks_or_yaml = repo.get(self.KEY_HOOKS, repo.get(self.KEY_YAML, {}))
            if self.KEY_YAML in repo:
                repo_list = Yaml(string=hooks_or_yaml).as_list
                suggested[self.KEY_REPOS].extend(repo_list)
            else:
                # TODO: show a deprecation warning for this case
                new_repo[self.KEY_HOOKS] = Yaml(string=hooks_or_yaml).as_data
                suggested[self.KEY_REPOS].append(new_repo)
        suggested.update(original)
        return Yaml(data=suggested).reformatted

    def check_rules(self) -> YieldFlake8Error:
        """Check the rules for the pre-commit hooks."""
        self.actual_yaml = Yaml(path=self.file_path)
        if self.KEY_REPOS not in self.actual_yaml.as_data:
            yield self.flake8_error(1, " doesn't have the {!r} root key".format(self.KEY_REPOS))
            return
        yield from self.check_root_values()
        yield from self.check_repos()

    def check_root_values(self) -> YieldFlake8Error:
        """Check the root values in the configuration file."""
        actual = self.actual_yaml.as_data.copy()
        actual.pop(self.KEY_REPOS, None)

        expected = dict(self.file_dict).copy()
        expected.pop(self.KEY_REPOS, None)

        yaml = Yaml(data=actual).compare_with_dictdiffer(expected)
        if yaml.missing_format:
            yield self.flake8_error(8, " has missing values:\n{}".format(yaml.missing_format.reformatted))
        if yaml.diff_format:
            yield self.flake8_error(9, " has different values:\n{}".format(yaml.diff_format.reformatted))

    def check_repos(self) -> YieldFlake8Error:
        """Check the repositories configured in pre-commit."""
        actual = self.actual_yaml.as_data.get(self.KEY_REPOS, [])  # type: List[YamlData]
        expected = self.file_dict.get(self.KEY_REPOS, [])  # type: List[OrderedDict]

        actual_repo_mapping = OrderedDict(
            {repo.get(self.KEY_REPO): repo for repo in actual}
        )  # type: OrderedDict[str, Yaml]
        for index, repo_data in enumerate(expected):
            if self.KEY_YAML in repo_data:
                yield from self.check_repo_yaml(actual_repo_mapping, repo_data)
                continue

            yield from self.check_repo_old_format(actual, index, repo_data)

    def check_repo_yaml(self, actual_repo_mapping: OrderedDict, repo_data: OrderedDict) -> YieldFlake8Error:
        """Check a repo with a YAML string configuration."""
        expected_repos_yaml = Yaml(string=repo_data.get(self.KEY_YAML))
        for expected_repo in expected_repos_yaml.as_list:
            repo_name = expected_repo["repo"]
            last_part = repo_name.split("/")[-1]
            if repo_name not in actual_repo_mapping:
                yield self.flake8_error(
                    2, ": repo {!r} not found. Use this:\n{}".format(last_part, expected_repos_yaml.reformatted)
                )
                continue

            # FIXME:
            # comparison = Yaml(dict_= actual_repo_mapping[repo_name]).compare_to(expected_repo)
            # if comparison.missing_format:
            #     yield self.flake8_error(
            #         1, " has missing values. Use this:\n{}".format(comparison.missing_format.reformatted)
            #     )
            # if comparison.diff_format:
            #     yield self.flake8_error(
            #         2, " has different values. Use this:\n{}".format(comparison.diff_format.reformatted)
            #     )

    def check_repo_old_format(self, actual_repos: YamlData, index: int, repo_data: OrderedDict) -> YieldFlake8Error:
        """Check repos using the old deprecated format with ``hooks`` and ``repo`` keys."""
        repo_name = repo_data.get(self.KEY_REPO)
        if not repo_name:
            yield self.flake8_error(2, ": style file is missing {!r} key in repo #{}".format(self.KEY_REPO, index))
            return

        actual_repo_dict = find_object_by_key(actual_repos, self.KEY_REPO, repo_name)
        if not actual_repo_dict:
            yield self.flake8_error(3, ": repo {!r} does not exist under {!r}".format(repo_name, self.KEY_REPOS))
            return

        if self.KEY_HOOKS not in actual_repo_dict:
            yield self.flake8_error(4, ": missing {!r} in repo {!r}".format(self.KEY_HOOKS, repo_name))
            return

        actual_hooks = actual_repo_dict.get(self.KEY_HOOKS) or []
        yaml_expected_hooks = repo_data.get(self.KEY_HOOKS)
        if not yaml_expected_hooks:
            yield self.flake8_error(5, ": style file is missing {!r} in repo {!r}".format(self.KEY_HOOKS, repo_name))
            return

        expected_hooks = Yaml(string=yaml_expected_hooks).as_data
        for expected_dict in expected_hooks:
            hook_id = expected_dict.get(self.KEY_ID)
            if not hook_id:
                expected_yaml = self.format_hook(expected_dict)
                yield self.flake8_error(
                    6, ": style file is missing {!r} in hook:\n{}".format(self.KEY_ID, expected_yaml)
                )
                continue
            actual_dict = find_object_by_key(actual_hooks, self.KEY_ID, hook_id)
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
