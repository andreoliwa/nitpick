"""YAML tests."""
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
    ).assert_file_contents(filename, expected_yaml)


def test_missing_different_values(tmp_path, datadir):
    """Test different and missing values on any YAML."""
    filename = "me/deep/rooted.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "existing-actual.yaml").style(
        datadir / "existing-desired.toml"
    ).api_check_then_fix(
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
              - c: 1
                b: 2
                a: 3
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
    ).assert_file_contents(
        filename, datadir / "existing-expected.yaml"
    )
