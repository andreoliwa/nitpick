"""Text file tests."""
import pytest

from tests.helpers import ProjectMock


@pytest.mark.xfail(reason="WIP")
def test_suggest_initial_contents(request):
    """Suggest initial contents for a text file."""
    ProjectMock(request).style(
        """
        [["requirements.txt".contains]]
        # File contains this exact line anywhere
        line = "sphinx>=1.3.0"
        """
    ).flake8().assert_errors_contain(
        """
        NIP341 File requirements.txt was not found. Create it with this content:\x1b[32m
        sphinx>=1.3.0\x1b[0m
        """
    )
