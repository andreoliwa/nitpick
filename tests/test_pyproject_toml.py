"""pyproject.toml tests."""
from nitpick.files.pyproject_toml import PyProjectTomlFile
from tests.helpers import ProjectMock


def test_pyproject_has_no_configuration(request):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(request).style("").pyproject_toml("").flake8().assert_no_errors()


def test_suggest_initial_contents(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).style(
        """
        [nitpick.files."pyproject.toml"]
        "missing_message" = "Do something"
        """
    ).flake8().assert_errors_contain("NIP311 File {} was not found. Do something".format(PyProjectTomlFile.file_name))
