"""YAML tests."""
from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.plugins.yaml import YamlPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_suggest_initial_contents(tmp_path, datadir):
    """Suggest contents when YAML files do not exist."""
    filename = ".github/workflows/python.yaml"
    expected_yaml = (datadir / "new-expected.yaml").read_text()
    ProjectMock(tmp_path).style(datadir / "new-desired.toml").api_check_then_fix(
        Fuss(
            True,
            filename,
            SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + YamlPlugin.violation_base_code,
            " was not found. Create it with this content:",
            expected_yaml,
        )
    ).assert_file_contents(filename, expected_yaml).api_check().assert_violations()


def test_missing_different_values(tmp_path, datadir):
    """Test different and missing values on any YAML."""
    filename = "me/deep/rooted.yaml"
    project = ProjectMock(tmp_path).save_file(filename, datadir / "existing-actual.yaml")
    project.style(datadir / "existing-desired.toml").api_check_then_fix(
        Fuss(
            True,
            filename,
            YamlPlugin.violation_base_code + SharedViolations.DIFFERENT_VALUES.code,
            " has different values. Use this:",
            """
            mixed:
              - lets:
                  ruin: this
                  with:
                    - weird
                    - '1'
                    - crap
              - second item: also a dict
            python:
              install:
                - extra_requirements:
                    - some
                    - nice
                    - package
              version: '3.9'
            """,
        ),
        Fuss(
            True,
            filename,
            YamlPlugin.violation_base_code + SharedViolations.MISSING_VALUES.code,
            " has missing values:",
            """
            root_key:
              a_dict:
                - c: '3.1'
                - b: 2
                - a: string value
              a_nested:
                int: 10
                list:
                  - 0
                  - 2
                  - 1
            """,
        ),
    ).assert_file_contents(filename, datadir / "existing-expected.yaml")
    project.api_check().assert_violations()


def test_pre_commit_repo_should_be_added_not_replaced(tmp_path, datadir):
    """Test a pre-commit repo being added to the list and not replacing an existing repo in the same position."""
    filename = PRE_COMMIT_CONFIG_YAML
    project = ProjectMock(tmp_path).save_file(filename, datadir / "1-actual-pre-commit-config.yaml")
    project.style(datadir / "1-desired.toml").api_check_then_fix(
        Fuss(
            True,
            filename,
            YamlPlugin.violation_base_code + SharedViolations.MISSING_VALUES.code,
            " has missing values:",
            """
            repos:
              - repo: https://github.com/myint/autoflake
                hooks:
                  - id: autoflake
                    args:
                      - --in-place
                      - --remove-all-unused-imports
                      - --remove-unused-variables
                      - --remove-duplicate-keys
                      - --ignore-init-module-imports
            """,
        ),
    ).assert_file_contents(filename, datadir / "1-expected-pre-commit-config.yaml")
    project.api_check().assert_violations()
