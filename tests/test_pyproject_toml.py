"""pyproject.toml tests."""
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from tests.helpers import ProjectMock


def test_missing_pyproject_toml(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).style(
        """
        ["pyproject.toml".nitpick]
        "missing_message" = "Do something"
        """
    ).lint().assert_errors_contain(f"NIP311 File: {PyProjectTomlFile.file_name}: Missing file. Do something")
