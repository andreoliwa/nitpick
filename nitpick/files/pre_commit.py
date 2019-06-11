# -*- coding: utf-8 -*-
"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from typing import Any, Dict, List, Optional, Tuple

import dictdiffer

from nitpick.files.base import BaseFile
from nitpick.formats import Yaml
from nitpick.generic import find_object_by_key
from nitpick.typedefs import YieldFlake8Error


class PreCommitFile(BaseFile):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""

    file_name = ".pre-commit-config.yaml"
    error_base_number = 330
    actual_yaml = None  # type: Optional[Yaml]

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
                # FIXME: deprecation warning
                new_repo[self.KEY_HOOKS] = Yaml(string=hooks_or_yaml).as_dict
                suggested[self.KEY_REPOS].append(new_repo)
        suggested.update(original)
        return Yaml(dict_=suggested).reformatted

    def check_rules(self) -> YieldFlake8Error:
        """Check the rules for the pre-commit hooks."""
        self.actual_yaml = Yaml(path=self.file_path)
        if self.KEY_REPOS not in self.actual_yaml.as_dict:
            yield self.flake8_error(1, " doesn't have the {!r} root key".format(self.KEY_REPOS))
            return
        yield from self.check_root_values()
        yield from self.check_repos()

    def check_root_values(self):
        """Check the root values in the configuration file."""
        actual = self.actual_yaml.as_dict.copy()
        actual.pop(self.KEY_REPOS, None)

        expected = dict(self.file_dict).copy()
        expected.pop(self.KEY_REPOS, None)

        for diff_type, key, values in dictdiffer.diff(actual, expected):
            if diff_type == dictdiffer.ADD:
                yield from self.show_missing_keys(key, values)
            elif diff_type == dictdiffer.CHANGE:
                yield from self.compare_different_keys(key, values[0], values[1])

    def check_repos(self):
        """Check the repositories configured in pre-commit."""
        actual = self.actual_yaml.as_dict.get(self.KEY_REPOS, [])  # type: List[dict]
        expected = self.file_dict.get(self.KEY_REPOS, [])  # type: List[dict]
        for index, configuration_data in enumerate(expected):
            if self.KEY_YAML in configuration_data:
                self.check_repo_yaml(configuration_data)
                continue

            repo_name = configuration_data.get(self.KEY_REPO)
            if not repo_name:
                yield self.flake8_error(2, ": style file is missing {!r} key in repo #{}".format(self.KEY_REPO, index))
                continue

            actual_repo_dict = find_object_by_key(actual, self.KEY_REPO, repo_name)
            if not actual_repo_dict:
                yield self.flake8_error(3, ": repo {!r} does not exist under {!r}".format(repo_name, self.KEY_REPOS))
                continue

            if self.KEY_HOOKS not in actual_repo_dict:
                yield self.flake8_error(4, ": missing {!r} in repo {!r}".format(self.KEY_HOOKS, repo_name))
                continue

            actual_hooks = actual_repo_dict.get(self.KEY_HOOKS) or []
            yaml_expected_hooks = configuration_data.get(self.KEY_HOOKS)
            if not yaml_expected_hooks:
                yield self.flake8_error(
                    5, ": style file is missing {!r} in repo {!r}".format(self.KEY_HOOKS, repo_name)
                )
                continue

            expected_hooks = Yaml(string=yaml_expected_hooks).as_dict
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

    def show_missing_keys(self, key, values: List[Tuple[str, Any]]):
        """Show the keys that are not present in a section."""
        output = Yaml(dict_=dict(values)).reformatted
        yield self.flake8_error(8, " has missing values:\n{}".format(output))

    # FIXME:
    # def show_missing_repos(self, values: List[Tuple[str, Any]]):
    #     yaml = YAML()
    #     yaml.map_indent = 2
    #     yaml.sequence_indent = 4
    #     yaml.sequence_dash_offset = 2
    #     yaml.stream = io.StringIO()
    #     data = {"repos": [data for index, data in values]}
    #     yaml.dump(data, yaml.stream)
    #     output = yaml.stream.getvalue()
    #     yield self.flake8_error(9, " has missing repos:\n{}".format(output))

    def compare_different_keys(self, key, raw_actual: Any, raw_expected: Any):
        """Compare different keys."""
        if isinstance(raw_actual, (int, float, bool)) or isinstance(raw_expected, (int, float, bool)):
            # A boolean "True" or "true" might have the same effect on YAML.
            actual = str(raw_actual).lower()
            expected = str(raw_expected).lower()
        else:
            actual = raw_actual
            expected = raw_expected
        if actual != expected:
            example = Yaml(dict_={key: raw_expected}).reformatted
            yield self.flake8_error(
                9, ": {!r} is {!r} but it should be like this:\n{}".format(key, raw_actual, example)
            )

    @staticmethod
    def format_hook(expected_dict) -> str:
        """Format the hook so it's easy to copy and paste it to the .yaml file: ID goes first, indent with spaces."""
        lines = Yaml(dict_=expected_dict).reformatted
        output = []  # type: List[str]
        for line in lines.split("\n"):
            if line.startswith("id:"):
                output.insert(0, "  - {}".format(line))
            else:
                output.append("    {}".format(line))
        return "\n".join(output)

    def check_repo_yaml(self, repo_dict):
        """Check a repo with a YAML string configuration."""
        yaml_str = repo_dict.get(self.KEY_YAML)
        assert yaml_str  # FIXME:
