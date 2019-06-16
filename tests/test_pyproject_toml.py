"""pyproject.toml tests."""
from nitpick.files.pyproject_toml import PyProjectTomlFile
from tests.helpers import ProjectMock


def test_pyproject_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").pyproject_toml("").lint().assert_errors_contain(
        "NIP312 File {} should be deleted".format(PyProjectTomlFile.file_name)
    )


def test_suggest_initial_contents(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).style(
        """
        [nitpick.files."pyproject.toml"]
        "missing_message" = "Do something"
        """
    ).lint().assert_errors_contain("NIP311 File {} was not found. Do something".format(PyProjectTomlFile.file_name))
