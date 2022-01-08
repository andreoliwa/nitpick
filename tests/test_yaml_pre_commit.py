"""Test .pre-commit-config.yaml."""
from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.plugins.yaml import YamlPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_repo_should_be_added_not_replaced(tmp_path, datadir):
    """Test a pre-commit repo being added to the list and not replacing an existing repo in the same position."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "uk-actual.yaml").style(
        datadir / "uk-default.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
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
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "uk-default-expected.yaml"
    ).api_check().assert_violations()


def test_clear_unique_key(tmp_path, datadir):
    """Test overriding the default unique key with nothing.

    The new element will be merged on top of the first list element.
    TODO Shouldn't the whole list be replaced by one single element? If there is a use case, change this behaviour.
    """
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "uk-actual.yaml").style(
        datadir / "uk-empty.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            369,
            " has different values. Use this:",
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
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "uk-empty-expected.yaml"
    ).api_check().assert_violations()


def test_use_another_attribute_as_unique_key(tmp_path, datadir):
    """Test overriding the default unique key with some other field."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "uk-actual.yaml").style(
        datadir / "uk-override.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: https://github.com/psf/black
                rev: 21.12b0
                hooks:
                  - id: autoflake
                    args:
                      - --wrong-id-for-the-black-repo
                      - --wont-be-validated-by-nitpick
            """,
        )
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "uk-override-expected.yaml"
    ).api_check().assert_violations()


def test_pre_commit_with_multiple_repos_should_not_change_if_repos_exist(tmp_path, datadir):
    """A real pre-commit config with multiple repos should not be changed if all the expected repos are there.."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml").style(
        datadir / "real.toml"
    ).api_check_then_fix(partial_names=[PRE_COMMIT_CONFIG_YAML]).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml"
    ).api_check(
        PRE_COMMIT_CONFIG_YAML
    ).assert_violations()


def test_repo_with_missing_key_value_pairs(tmp_path, datadir):
    """Test a repo (nested dict) with missing key/value pairs."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "hook-args.yaml").style(
        datadir / "hook-args-add.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: https://github.com/pre-commit/pygrep-hooks
                hooks:
                  - id: python-no-eval
                    args:
                      - --first
                      - --second
                    another: value
                    last: key
            """,
        )
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "hook-args-add.yaml"
    ).api_check().assert_violations()


def test_repo_with_different_key_value_pairs(tmp_path, datadir):
    """Test a nested dict with different key/value pairs, e.g.: different args or dependencies."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "hook-args.yaml").style(
        datadir / "hook-args-change.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: https://github.com/psf/black
                hooks:
                  - id: black
                    args:
                      - --safe
                      - --custom
                      - --loud
              - repo: https://github.com/asottile/blacken-docs
                hooks:
                  - id: blacken-docs
                    additional_dependencies:
                      - black==22.1
            """,
        )
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "hook-args-change.yaml"
    ).api_check().assert_violations()
