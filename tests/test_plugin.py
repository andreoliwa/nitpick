"""Plugin tests."""
import pytest
from flake8.main import cli

from nitpick.app import Nitpick
from nitpick.constants import READ_THE_DOCS_URL
from tests.helpers import ProjectMock


def _call_main(argv, retv=0):
    """Call flake8's main CLI entry point.

    This is how flake8 itself runs CLI tests.
    Copied from:
    https://gitlab.com/pycqa/flake8/-/blob/master/tests/integration/test_main.py#L12-15
    """
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv)
    assert excinfo.value.code == retv


def test_nitpick_offline_flag(tmpdir):
    """Test if the offline flag was set."""
    with tmpdir.as_cwd():
        _call_main([])
        assert Nitpick.current_app().offline is False

        _call_main(["--nitpick-offline"])
        assert Nitpick.current_app().offline is True


def test_absent_files(request):
    """Test absent files from the style configuration."""
    ProjectMock(request).style(
        """
        [nitpick.files.absent]
        xxx = "Remove this"
        yyy = "Remove that"
        """
    ).touch_file("xxx").touch_file("yyy").flake8().assert_errors_contain(
        "NIP104 File xxx should be deleted: Remove this"
    ).assert_errors_contain(
        "NIP104 File yyy should be deleted: Remove that"
    )


def test_files_beginning_with_dot(request):
    """Test files beginning with a dot: the can't be used on [nitpick.files] (for now)."""
    ProjectMock(request).style(
        """
        [nitpick.files.".editorconfig"]
        missing_message = "Create this file"
        """
    ).flake8().assert_errors_contain(
        """NIP001 File nitpick-style.toml has an incorrect style. Invalid TOML (toml.decoder"""
        + """.TomlDecodeError: Invalid group name \'editorconfig"\'. Try quoting it. (line 1 column 1 char 0))"""
    )


def test_missing_message(request):
    """Test if the breaking style change "missing_message" key points to the correct help page."""
    project = (
        ProjectMock(request)
        .style(
            """
        [nitpick.files."pyproject.toml"]
        missing_message = "Install poetry and run 'poetry init' to create it"
        """
        )
        .flake8()
    )
    project.assert_errors_contain(
        """
        NIP001 File nitpick-style.toml has an incorrect style. Invalid config:\x1b[32m
        nitpick.files."pyproject.toml": Unknown file. See {}nitpick_section.html#nitpick-files.\x1b[0m
        """.format(
            READ_THE_DOCS_URL
        )
    )


def test_present_files(request):
    """Test present files from the style configuration."""
    ProjectMock(request).style(
        """
        [nitpick.files.present]
        ".editorconfig" = "Create this file"
        ".env" = ""
        "another-file.txt" = ""
        """
    ).flake8().assert_errors_contain("NIP103 File .editorconfig should exist: Create this file").assert_errors_contain(
        "NIP103 File .env should exist"
    ).assert_errors_contain(
        "NIP103 File another-file.txt should exist", 3
    )
