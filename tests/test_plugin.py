"""Plugin tests."""
import os
from enum import Enum
from unittest import mock

import pytest
import requests
from flake8.main import cli

from nitpick.cli import _FlagMixin
from nitpick.constants import READ_THE_DOCS_URL
from nitpick.core import Nitpick
from nitpick.violations import Fuss
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
    ).touch_file("xxx").touch_file("yyy").simulate_run().assert_errors_contain(
        "NIP104 File xxx should be deleted: Remove this"
    ).assert_errors_contain(
        "NIP104 File yyy should be deleted: Remove that"
    ).assert_fusses_are_exactly(
        Fuss(filename="xxx", code=104, message=" should be deleted: Remove this", suggestion="", lineno=1),
        Fuss(filename="yyy", code=104, message=" should be deleted: Remove that", suggestion="", lineno=1),
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
        .simulate_run()
    )
    project.assert_errors_contain(
        f"""
        NIP001 File nitpick-style.toml has an incorrect style. Invalid config:\x1b[32m
        nitpick.files."pyproject.toml": Unknown file. See {READ_THE_DOCS_URL}nitpick_section.html#nitpick-files.\x1b[0m
        """
    ).assert_fusses_are_exactly(
        Fuss(
            filename="nitpick-style.toml",
            code=1,
            message=" has an incorrect style. Invalid config:",
            # pylint: disable=line-too-long
            suggestion=f"""nitpick.files."pyproject.toml": Unknown file. See {READ_THE_DOCS_URL}nitpick_section.html#nitpick-files.""",
            lineno=1,
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
    ).simulate_run().assert_errors_contain(
        "NIP103 File .editorconfig should exist: Create this file"
    ).assert_errors_contain(
        "NIP103 File .env should exist"
    ).assert_errors_contain(
        "NIP103 File another-file.txt should exist", 3
    ).assert_fusses_are_exactly(
        Fuss(filename=".editorconfig", code=103, message=" should exist: Create this file", suggestion="", lineno=1),
        Fuss(filename=".env", code=103, message=" should exist", suggestion="", lineno=1),
        Fuss(filename="another-file.txt", code=103, message=" should exist", suggestion="", lineno=1),
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
        assert Nitpick.singleton().offline is False

        _call_main(["--nitpick-offline"])
        assert Nitpick.singleton().offline is True

        os.environ["NITPICK_OFFLINE"] = "1"
        _call_main([])
        assert Nitpick.singleton().offline is True


@mock.patch("requests.get")
def test_offline_doesnt_raise_connection_error(mocked_get, request):
    """On offline mode, no requests are made, so no connection errors should be raised."""
    mocked_get.side_effect = requests.ConnectionError("A forced error")
    ProjectMock(request).simulate_run(offline=True)


@mock.patch("requests.get")
def test_offline_recommend_using_flag(mocked_get, request, capsys):
    """Recommend using the flag on a connection error."""
    mocked_get.side_effect = requests.ConnectionError("error message from connection here")
    ProjectMock(request).simulate_run(call_api=False)
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "Your network is unreachable. Fix your connection or use --nitpick-offline / NITPICK_OFFLINE=1\n"
