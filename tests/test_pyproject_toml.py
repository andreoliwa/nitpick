"""pyproject.toml tests."""
from nitpick.constants import PYPROJECT_TOML
from tests.helpers import ProjectMock


def test_pyproject_has_no_configuration(request):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(request).style("").pyproject_toml("").simulate_run().assert_no_errors()


def test_suggest_initial_contents(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).style(
        """
        [nitpick.files.present]
        "pyproject.toml" = "Do something"
        """
    ).simulate_run().assert_errors_contain(
        f"NIP103 File {PYPROJECT_TOML} should exist: Do something"
    ).assert_cli_output(
        f"{PYPROJECT_TOML}:1: NIP103  should exist: Do something", violations=1
    )
