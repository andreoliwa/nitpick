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


def test_text_configuration(request):
    """Test configuration for text files."""
    # pylint: disable=line-too-long
    ProjectMock(request).style(
        """
        [["abc.txt".contains]]
        invalid = "key"
        line = ["it", "should", "be", "a", "string"]

        ["def.txt".contains]
        should_be = "inside an array"

        ["ghi.txt".whatever]
        wrong = "everything"
        """
    ).flake8().assert_errors_contain(
        """
        NIP001 File nitpick-style.toml has an incorrect style. Invalid config:\x1b[32m
        "abc.txt".contains.0.invalid: Unknown configuration. See https://nitpick.rtfd.io/en/latest/plugins.html#text-files.
        "abc.txt".contains.0.line: Not a valid string.
        "def.txt".contains: Not a valid list.
        "ghi.txt".whatever: Unknown configuration. See https://nitpick.rtfd.io/en/latest/plugins.html#text-files.\x1b[0m
        """,
        1,
    )


def test_text_file_contains_line(request):
    """Test if the text file contains a line."""
    ProjectMock(request).style(
        """
        [["my.txt".contains]]
        line = "qqq"
        [["my.txt".contains]]
        line = "abc"
        [["my.txt".contains]]
        line = "www"
        """
    ).save_file("my.txt", "def\nghi\nwww").flake8().assert_errors_contain(
        """
        NIP352 File my.txt has missing lines:\x1b[32m
        abc
        qqq\x1b[0m
        """
    )
