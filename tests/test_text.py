"""Text file tests."""

from nitpick.constants import READ_THE_DOCS_URL
from nitpick.violations import Fuss
from tests.helpers import NBSP, SUGGESTION_BEGIN, SUGGESTION_END, ProjectMock


def test_suggest_initial_contents(tmp_path):
    """Suggest initial contents for a text file."""
    ProjectMock(tmp_path).style(
        """
        [["requirements.txt".contains]]
        # File contains this exact line anywhere
        line = "sphinx>=1.3.0"

        [["requirements.txt".contains]]
        line = "some-package==1.0.0"
        """
    ).api_check_then_fix(
        Fuss(
            False,
            "requirements.txt",
            351,
            " was not found. Create it with this content:",
            """
            sphinx>=1.3.0
            some-package==1.0.0
            """,
        )
    )


def test_text_configuration(tmp_path):
    """Test configuration for text files."""
    # pylint: disable=line-too-long
    ProjectMock(tmp_path).style(
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
        f"""
        NIP001 File nitpick-style.toml has an incorrect style. Invalid config:{SUGGESTION_BEGIN}
        "abc.txt".contains.0.invalid: Unknown configuration. See {READ_THE_DOCS_URL}plugins.html#text-files.
        "abc.txt".contains.0.line: Not a valid string.
        "def.txt".contains: Not a valid list.
        "ghi.txt".whatever: Unknown configuration. See {READ_THE_DOCS_URL}plugins.html#text-files.{SUGGESTION_END}
        """,
        1,
    )


def test_text_file_contains_line(tmp_path):
    """Test if the text file contains a line."""
    ProjectMock(tmp_path).style(
        """
        [["my.txt".contains]]
        line = "qqq"
        [["my.txt".contains]]
        line = "abc"
        [["my.txt".contains]]
        line = "www"
        """
    ).save_file("my.txt", "def\nghi\nwww").api_check_then_fix(
        Fuss(
            False,
            "my.txt",
            352,
            " has missing lines:",
            """
            abc
            qqq
            """,
        )
    )


def test_yaml_file_as_text(tmp_path):
    """A YAML file is also a text file, so it could be checked with the text plugin."""
    ProjectMock(tmp_path).style(
        """
        [[".gitlab-ci.yml".contains]]
        line = "    - mypy -p ims --junit-xml report-mypy.xml"
        """
    ).save_file(".gitlab-ci.yml", "def\nghi\nwww").api_check_then_fix(
        Fuss(
            False, ".gitlab-ci.yml", 352, " has missing lines:", f"{NBSP * 4}- mypy -p ims --junit-xml report-mypy.xml"
        )
    )
