"""pyproject.toml tests."""
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from tests.helpers import ProjectMock


def test_missing_pyproject_toml(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    ProjectMock(request, pyproject_toml=False).lint().assert_errors_contain(
        f"NIP201 {PyProjectTomlFile.file_name} does not exist. Install poetry and run 'poetry init' to create it."
    )
