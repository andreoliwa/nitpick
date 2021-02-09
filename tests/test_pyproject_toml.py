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
    ).simulate_run().assert_errors_contain(
        f"NIP103 File {PYPROJECT_TOML} should exist: Do something"
    ).assert_cli_output(
        f"{PYPROJECT_TOML}:1: NIP103  should exist: Do something", violations=1
    )


def test_missing_different_values(tmp_path):
    """Test missing and different values."""
    ProjectMock(tmp_path).style(
        """
        ["pyproject.toml".something]
        yadayada = "no"
        """
    ).pyproject_toml(
        """
        [something]
        x = 1
        yadayada = "oh yes"
        abc = "123"
        """
    ).api().assert_fusses_are_exactly(
        Fuss(
            PYPROJECT_TOML,
            319,
            " has different values. Use this:",
            """
            [something]
            yadayada = "no"
            """,
        )
    )
    # FIXME[AA]: test missing
