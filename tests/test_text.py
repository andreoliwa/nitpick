"""Text file tests."""
from tests.helpers import ProjectMock


def test_suggest_initial_contents(request):
    """Suggest initial contents for a text file."""
    ProjectMock(request).style(
        """
        [["requirements.txt".contains]]
        # File contains this exact line anywhere
        line = "sphinx>=1.3.0"

        [["requirements.txt".contains]]
        line = "some-package==1.0.0"
        """
    ).flake8().assert_errors_contain(
        """
        NIP351 File requirements.txt was not found. Create it with this content:\x1b[32m
        sphinx>=1.3.0
        some-package==1.0.0\x1b[0m
        """
    )
