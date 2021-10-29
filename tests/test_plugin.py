"""Plugin tests."""
import os
from enum import Enum

import pytest
import responses
from flake8.main import cli

from nitpick.constants import READ_THE_DOCS_URL
from nitpick.core import Nitpick
from nitpick.enums import _OptionMixin
from nitpick.violations import Fuss
from tests.helpers import ProjectMock


def _call_main(argv, retv=0):
    """Call flake8's main CLI entry point.

    This is how flake8 itself runs CLI tests.
    Copied from:
    https://github.com/PyCQA/flake8/blob/master/tests/integration/test_main.py#L12-15
    """
    with pytest.raises(SystemExit) as excinfo:
        cli.main(argv)
    assert excinfo.value.code == retv


def test_absent_files(tmp_path):
    """Test absent files from the style configuration."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files.absent]
        xxx = "Remove this"
        yyy = "Remove that"
        """
    ).touch_file("xxx").touch_file("yyy").api_check_then_fix(
        Fuss(False, "xxx", 104, " should be deleted: Remove this"),
        Fuss(False, "yyy", 104, " should be deleted: Remove that"),
    )


def test_missing_message(tmp_path):
    """Test if the breaking style change "missing_message" key points to the correct help page."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files."pyproject.toml"]
        missing_message = "Install poetry and run 'poetry init' to create it"
        """
    ).api_check_then_fix(
        # pylint: disable=line-too-long
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid config:",
            f"""nitpick.files."pyproject.toml": Unknown file. See {READ_THE_DOCS_URL}nitpick_section.html#nitpick-files.""",
        )
    )


def test_present_files(tmp_path):
    """Test present files from the style configuration."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files.present]
        ".editorconfig" = "Create this file"
        ".env" = ""
        "another-file.txt" = ""
        """
    ).api_check_then_fix(
        Fuss(False, ".editorconfig", 103, " should exist: Create this file"),
        Fuss(False, ".env", 103, " should exist"),
        Fuss(False, "another-file.txt", 103, " should exist"),
    )


def test_flag_format_env_variable():
    """Test flag formatting and env variable."""

    class OtherFlags(_OptionMixin, Enum):
        """Some flags to be used on the assertions below."""

        MULTI_WORD = 1
        SOME_OPTION = 2

    assert OtherFlags.MULTI_WORD.as_flake8_flag() == "--nitpick-multi-word"
    os.environ["NITPICK_SOME_OPTION"] = "something"
    assert OtherFlags.SOME_OPTION.as_envvar() == "NITPICK_SOME_OPTION"
    assert OtherFlags.SOME_OPTION.get_environ() == "something"
    assert OtherFlags.MULTI_WORD.get_environ() == ""


def test_offline_flag_env_variable(tmpdir):
    """Test if the offline flag or environment variable was set."""
    with tmpdir.as_cwd():
        _call_main([])
        assert Nitpick.singleton().offline is False

        _call_main(["--nitpick-offline"])
        assert Nitpick.singleton().offline is True

        os.environ["NITPICK_OFFLINE"] = "1"
        _call_main([])
        assert Nitpick.singleton().offline is True


@responses.activate
def test_offline_doesnt_raise_connection_error(tmp_path):
    """On offline mode, no requests are made, so no connection errors should be raised."""
    responses.add(responses.GET, "https://api.github.com/repos/andreoliwa/nitpick", '{"default_branch": "develop"}')
    ProjectMock(tmp_path).flake8(offline=True)


@responses.activate
def test_offline_recommend_using_flag(tmp_path, capsys):
    """Recommend using the flag on a connection error."""
    responses.add(responses.GET, "https://api.github.com/repos/andreoliwa/nitpick", '{"default_branch": "develop"}')

    ProjectMock(tmp_path).flake8()
    out, err = capsys.readouterr()
    assert out == ""
    assert (
        "could not be downloaded. Either your network is unreachable or the URL is broken."
        " Check the URL, fix your connection, or use  --nitpick-offline / NITPICK_OFFLINE=1" in err
    )
