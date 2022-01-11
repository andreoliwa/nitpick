"""YAML tests."""
import warnings

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
            369,
            " has different values. Use this:",
            """
            python:
              version: '3.9'
            """,
        ),
        Fuss(
            True,
            filename,
            368,
            " has missing values:",
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


# FIXME: test list of dicts: by default, objects are compared by hash and new ones are added
