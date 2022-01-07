"""YAML tests."""
import warnings

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


def test_repos_yaml_key_deprecated(tmp_path, shared_datadir):
    """Test the deprecated "repos.yaml" key in the old style."""
    with warnings.catch_warnings(record=True) as captured:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")

        ProjectMock(tmp_path).style(shared_datadir / "pre-commit-config-with-old-repos-yaml-key.toml").pre_commit(
            """
            repos:
              - repo: not checked yet
                hooks:
                  - id: my-hook
            """
        ).api_check().assert_violations()

        assert len(captured) == 1
        assert issubclass(captured[-1].category, DeprecationWarning)
        assert (
            "The repos.yaml key is not supported anymore."
            " Check the documentation and please update your YAML styles" in str(captured[-1].message)
        )


def test_unique_key_pre_commit_repo_should_be_added_not_replaced(tmp_path, datadir):
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


def test_unique_key_override_with_nothing(tmp_path, datadir):
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


def test_unique_key_override_with_other_field(tmp_path, datadir):
    """Test overriding the default unique key with some other field."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "uk-actual.yaml").style(
        datadir / "uk-override.toml"
    ).api_check_then_fix(
        # FIXME: document this case
        # TODO: the "repo" key already exists with the same value; for now, no change will be made to the file
        # Fuss(
        #     True,
        #     PRE_COMMIT_CONFIG_YAML,
        #     368,
        #     " has missing values:",
        #     """
        #     repos:
        #       - repo: https://github.com/psf/black
        #         hooks:
        #           - id: autoflake
        #             args:
        #               - --wrong-id-for-the-black-repo
        #               - --wont-be-validated-by-nitpick
        #     """,
        # )
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "uk-override-expected.yaml"
    ).api_check().assert_violations()


# FIXME: test adding a default unique to some other file with a list of objects
# [".pre-commit-config.yaml".__search_unique_key]
# repos = "hooks[].name"
def test_pre_commit_with_multiple_repos_should_not_change_if_repos_exist(tmp_path, datadir):
    """A real pre-commit config with multiple repos should not be changed if all the expected repos are there.."""
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml").style(
        datadir / "real.toml"
    ).api_check_then_fix(partial_names=[PRE_COMMIT_CONFIG_YAML]).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml"
    ).api_check(
        PRE_COMMIT_CONFIG_YAML
    ).assert_violations()


def test_nested_dict_with_additional_key_value_pairs(tmp_path, datadir):
    """Test a nested dict with additional key/value pairs."""
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
