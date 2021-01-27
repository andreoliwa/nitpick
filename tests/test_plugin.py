"""Plugin tests."""
import os
from enum import Enum
from unittest import mock

import pytest
import requests
from flake8.main import cli

from nitpick.app import create_app
from nitpick.cli import _FlagMixin
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


def test_flag_format_env_variable():
    """Test flag formatting and env variable."""

    class OtherFlags(_FlagMixin, Enum):
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
        assert create_app().offline is False

        _call_main(["--nitpick-offline"])
        assert create_app().offline is True

        os.environ["NITPICK_OFFLINE"] = "1"
        _call_main([])
        assert create_app().offline is True


@mock.patch("requests.get")
def test_offline_doesnt_raise_connection_error(mocked_get, request):
    """On offline mode, no requests are made, so no connection errors should be raised."""
    mocked_get.side_effect = requests.ConnectionError("A forced error")
    ProjectMock(request).flake8(offline=True)


@mock.patch("requests.get")
def test_offline_recommend_using_flag(mocked_get, request, capsys):
    """Recommend using the flag on a connection error."""
    mocked_get.side_effect = requests.ConnectionError("error message from connection here")
    ProjectMock(request).flake8()
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Your network is unreachable. Fix your connection or use --nitpick-offline / NITPICK_OFFLINE=1\n"
