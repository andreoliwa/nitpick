"""YAML tests."""
from nitpick.plugins.yaml import YamlPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_suggest_initial_contents(tmp_path):
    """Suggest contents when YAML files do not exist."""
    pass  # FIXME:
    # filename = "my.toml"
    # expected_toml = """
    #     [section]
    #     key = "value"
    #     number = 10
    # """
    # ProjectMock(tmp_path).style(
    #     f"""
    #     ["{filename}".section]
    #     key = "value"
    #     number = 10
    #     """
    # ).api_check_then_fix(
    #     Fuss(
    #         True,
    #         filename,
    #         SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + TomlPlugin.violation_base_code,
    #         " was not found. Create it with this content:",
    #         expected_toml,
    #     )
    # ).assert_file_contents(
    #     filename, expected_toml
    # )


def test_missing_different_values(tmp_path, datadir):
    """Test different and missing values on any YAML."""
    filename = "actual.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / filename).style(datadir / "style.toml").api_check_then_fix(
        Fuss(
            False,
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
            False,
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
    )  # FIXME: .assert_file_contents(filename, datadir / "expected.yaml")
