"""pyproject.toml tests."""
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from tests.helpers import ProjectMock


def test_pyproject_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").pyproject_toml("").lint().assert_errors_contain(
        f"NIP312 File {PyProjectTomlFile.file_name} should be deleted"
    )


def test_missing_pyproject_toml(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).style(
        """
        [nitpick.files."pyproject.toml"]
        "missing_message" = "Do something"
        """
    ).lint().assert_errors_contain(f"NIP311 File {PyProjectTomlFile.file_name} was not found. Do something")
