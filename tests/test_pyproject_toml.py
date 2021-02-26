"""pyproject.toml tests."""
from nitpick.constants import PYPROJECT_TOML
from nitpick.violations import Fuss
from tests.helpers import ProjectMock


def test_pyproject_has_no_configuration(tmp_path):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(tmp_path).style("").pyproject_toml("").simulate_run().assert_no_errors()


def test_suggest_initial_contents(tmp_path):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(tmp_path, pyproject_toml=False).style(
        """
        [nitpick.files.present]
        "pyproject.toml" = "Do something"
        """
    ).simulate_run().assert_errors_contain(f"NIP103 File {PYPROJECT_TOML} should exist: Do something").cli_run(
        f"{PYPROJECT_TOML}:1: NIP103  should exist: Do something", violations=1
    )


def test_missing_different_values(tmp_path):
    """Test missing and different values."""
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
    ).api_apply().assert_violations(
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
