"""YAML tests."""
from nitpick.plugins.yaml import YamlPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_suggest_initial_contents(tmp_path, datadir):
    """Suggest contents when YAML files do not exist."""
    filename = ".github/workflows/python.yaml"
    expected_yaml = (datadir / "2-expected.yaml").read_text()
    ProjectMock(tmp_path).style(datadir / "2-desired.toml").api_check_then_fix(
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
    filename = "1-actual.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / filename).style(datadir / "1-desired.toml").api_check_then_fix(
        Fuss(
            True,
            filename,
            YamlPlugin.violation_base_code + SharedViolations.DIFFERENT_VALUES.code,
            " has different values. Use this:",
            """
            python:
              install:
                - extra_requirements:
                    - item1
                    - item2
                    - item3
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
                - a: string value
                - b: 2
                - c: '3.1'
              a_nested:
                int: 10
                list:
                  - 0
                  - 1
                  - 2
            """,
        ),
    )  # FIXME:  .assert_file_contents(filename, datadir / "1-expected.yaml")
