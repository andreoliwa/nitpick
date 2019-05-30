# -*- coding: utf-8 -*-
"""Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""
from typing import Any, Dict, List, Tuple

import dictdiffer
import yaml

from flake8_nitpick.files.base import BaseFile
from flake8_nitpick.generic import find_object_by_key
from flake8_nitpick.typedefs import YieldFlake8Error


class PreCommitFile(BaseFile):
    """Checker for the `.pre-commit-config.yaml <https://pre-commit.com/#pre-commit-configyaml---top-level>`_ file."""

    file_name = ".pre-commit-config.yaml"
    error_base_number = 330

    KEY_REPOS = "repos"
    KEY_HOOKS = "hooks"
    KEY_REPO = "repo"
    KEY_ID = "id"

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        suggested = dict(self.file_dict).copy()
        for repo in suggested.get(self.KEY_REPOS, []):
            repo[self.KEY_HOOKS] = yaml.safe_load(repo[self.KEY_HOOKS])
        return yaml.dump(suggested, default_flow_style=False)

    def check_rules(self) -> YieldFlake8Error:
        """Check the rules for the pre-commit hooks."""
        actual = yaml.safe_load(self.file_path.open()) or {}
        if self.KEY_REPOS not in actual:
            yield self.flake8_error(1, f" doesn't have the {self.KEY_REPOS!r} root key")
            return

        actual_root = actual.copy()
        actual_root.pop(self.KEY_REPOS, None)
        expected_root = dict(self.file_dict).copy()
        expected_root.pop(self.KEY_REPOS, None)
        for diff_type, key, values in dictdiffer.diff(expected_root, actual_root):
            if diff_type == dictdiffer.REMOVE:
                yield from self.show_missing_keys(key, values)
            elif diff_type == dictdiffer.CHANGE:
                yield from self.compare_different_keys(key, values[0], values[1])

        yield from self.check_repos(actual)

    def check_repos(self, actual: Dict[str, Any]):
        """Check the repositories configured in pre-commit."""
        actual_repos: List[dict] = actual[self.KEY_REPOS] or []
        expected_repos: List[dict] = self.file_dict.get(self.KEY_REPOS, [])
        for index, expected_repo_dict in enumerate(expected_repos):
            repo_name = expected_repo_dict.get(self.KEY_REPO)
            if not repo_name:
                yield self.flake8_error(2, f": style file is missing {self.KEY_REPO!r} key in repo #{index}")
                continue

            actual_repo_dict = find_object_by_key(actual_repos, self.KEY_REPO, repo_name)
            if not actual_repo_dict:
                yield self.flake8_error(3, f": repo {repo_name!r} does not exist under {self.KEY_REPOS!r}")
                continue

            if self.KEY_HOOKS not in actual_repo_dict:
                yield self.flake8_error(4, f": missing {self.KEY_HOOKS!r} in repo {repo_name!r}")
                continue

            actual_hooks = actual_repo_dict.get(self.KEY_HOOKS) or []
            yaml_expected_hooks = expected_repo_dict.get(self.KEY_HOOKS)
            if not yaml_expected_hooks:
                yield self.flake8_error(5, f": style file is missing {self.KEY_HOOKS!r} in repo {repo_name!r}")
                continue

            expected_hooks: List[dict] = yaml.safe_load(yaml_expected_hooks)
            for expected_dict in expected_hooks:
                hook_id = expected_dict.get(self.KEY_ID)
                if not hook_id:
                    expected_yaml = self.format_hook(expected_dict)
                    yield self.flake8_error(6, f": style file is missing {self.KEY_ID!r} in hook:\n{expected_yaml}")
                    continue
                actual_dict = find_object_by_key(actual_hooks, self.KEY_ID, hook_id)
                if not actual_dict:
                    expected_yaml = self.format_hook(expected_dict)
                    yield self.flake8_error(7, f": missing hook with id {hook_id!r}:\n{expected_yaml}")
                    continue

    def show_missing_keys(self, key, values: List[Tuple[str, Any]]):
        """Show the keys that are not present in a section."""
        missing = dict(values)
        output = yaml.dump(missing, default_flow_style=False)
        yield self.flake8_error(8, f" has missing values:\n{output}")

    def compare_different_keys(self, key, raw_expected: Any, raw_actual: Any):
        """Compare different keys."""
        if isinstance(raw_actual, (int, float, bool)) or isinstance(raw_expected, (int, float, bool)):
            # A boolean "True" or "true" might have the same effect on YAML.
            actual = str(raw_actual).lower()
            expected = str(raw_expected).lower()
        else:
            actual = raw_actual
            expected = raw_expected
        if actual != expected:
            example = yaml.dump({key: raw_expected}, default_flow_style=False)
            yield self.flake8_error(9, f": {key!r} is {raw_actual!r} but it should be like this:\n{example}")

    @staticmethod
    def format_hook(expected_dict: dict) -> str:
        """Format the hook so it's easy to copy and paste it to the .yaml file: ID goes first, indent with spaces."""
        lines = yaml.dump(expected_dict, default_flow_style=False)
        output: List[str] = []
        for line in lines.split("\n"):
            if line.startswith("id:"):
                output.insert(0, f"  - {line}")
            else:
                output.append(f"    {line}")
        return "\n".join(output)
