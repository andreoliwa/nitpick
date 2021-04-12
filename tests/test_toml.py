"""pyproject.toml tests."""
from nitpick.constants import PYPROJECT_TOML
from nitpick.plugins.toml import TomlPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_pyproject_has_no_configuration(tmp_path):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(tmp_path).style("").pyproject_toml("").api_check_then_apply()


def test_pyproject_toml_file_present(tmp_path):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(tmp_path, pyproject_toml=False).style(
        """
        [nitpick.files.present]
        "pyproject.toml" = "Do something"
        """
    ).api_check_then_apply(Fuss(False, PYPROJECT_TOML, 103, " should exist: Do something")).cli_run(
        f"{PYPROJECT_TOML}:1: NIP103  should exist: Do something", violations=1
    )


# def test_suggest_initial_contents(tmp_path): # FIXME[AA]:
#     """Suggest contents when TOML files do not exist."""
#     file = "my.toml"
#     expected_toml = """
#         [section]
#         key = "value"
#         number = 10
#     """
#     ProjectMock(tmp_path).style(
#         f"""
#         ["{file}".section]
#         key = "value"
#         number = 10
#         """
#     ).api_check_then_apply(
#         Fuss(
#             True,
#             file,
#             SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + TomlPlugin.violation_base_code,
#             " was not found. Create it with this content:",
#             expected_toml,
#         )
#     ).assert_file_contents(
#         file, expected_toml
#     )


def test_missing_different_values_pyproject_toml(tmp_path):
    """Test missing and different values on pyproject.toml."""
    ProjectMock(tmp_path).style(
        """
        ["pyproject.toml".something]
        yada = "after"

        ["pyproject.toml".tool]
        missing = "value"
        """
    ).pyproject_toml(
        """
        [something]
        x = 1  # comment for x
        yada = "before"  # comment for yada yada
        abc = "123" # comment for abc
        """
    ).api_check_then_apply(
        Fuss(
            True,
            PYPROJECT_TOML,
            319,
            " has different values. Use this:",
            """
            [something]
            yada = "after"
            """,
        ),
        Fuss(
            True,
            PYPROJECT_TOML,
            318,
            " has missing values:",
            """
            [tool]
            missing = "value"
            """,
        ),
    ).assert_file_contents(
        PYPROJECT_TOML,
        """
        [something]
        x = 1  # comment for x
        yada = "after"  # comment for yada yada
        abc = "123" # comment for abc

        [tool]
        missing = "value"
        """,
    )


def test_missing_different_values_any_toml(tmp_path):
    """Test different and missing keys/values on any TOML."""
    filename = "any.toml"
    ProjectMock(tmp_path).save_file(
        filename,
        """
        [section]
        # Line comment
        key = "original value"
        """,
    ).style(
        f"""
        ["{filename}".section]
        key = "new value"
        number = 5
        """
    ).api_check_then_apply(
        Fuss(
            True,
            filename,
            TomlPlugin.violation_base_code + SharedViolations.DIFFERENT_VALUES.code,
            " has different values. Use this:",
            """
            [section]
            key = "new value"
            """,
        ),
        Fuss(
            True,
            filename,
            TomlPlugin.violation_base_code + SharedViolations.MISSING_VALUES.code,
            " has missing values:",
            """
            [section]
            number = 5
            """,
        ),
    ).assert_file_contents(
        filename,
        """
        [section]
        # Line comment
        key = "new value"
        number = 5
        """,
    )
