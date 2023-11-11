"""CLI tests."""
from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest import mock

import pytest
import tomlkit

from nitpick import __version__
from nitpick.constants import (
    CONFIG_TOOL_NITPICK_KEY,
    DOT_NITPICK_TOML,
    PYTHON_PYPROJECT_TOML,
    READ_THE_DOCS_URL,
    EmojiEnum,
)
from nitpick.style import StyleManager
from tests.helpers import BLANK_LINE, ProjectMock


def test_simple_error(tmp_path: Path) -> None:
    """A simple error on the CLI."""
    project = (
        ProjectMock(tmp_path)
        .style(
            """
            ["pyproject.toml".tool.black]
            line-length = 100
            """
        )
        .pyproject_toml(
            """
            [tool.blabla]
            something = 22
            """
        )
    )

    project.cli_run(
        f"""
        {project.root_dir / "pyproject.toml"!s}:1: NIP318  has missing values:
        [tool.black]
        line-length = 100
        """
    )


def test_missing_style_and_suggest_option(tmp_path: Path) -> None:
    """Print error if both style and --suggest options are missing."""
    ProjectMock(tmp_path).cli_init(
        f"Nothing to do. {EmojiEnum.SLEEPY_FACE.value} Either pass at least one style URL"
        " or use --suggest to add styles based on the files in the project root"
        " (you can do both at the same time)."
    )


@pytest.mark.parametrize("config_file", [DOT_NITPICK_TOML, PYTHON_PYPROJECT_TOML])
@pytest.mark.skip(reason="WIP")  # TODO(AA): fix the test
def test_config_file_already_has_tool_nitpick_section(tmp_path: Path, config_file: str) -> None:
    """Test if both config files already exist."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True).save_file(
        config_file,
        f"""
        [{CONFIG_TOOL_NITPICK_KEY}]
        style = ['/this/should/not/be/validated-yet.toml']
        """,
    )
    project.cli_init(
        [
            f"The config file {config_file!r} already has a [{CONFIG_TOOL_NITPICK_KEY}] section.",
            "style = ['/this/should/not/be/validated-yet.toml']",
        ],
        exit_code=1,
    )


@pytest.fixture()
def style_dir_with_types(shared_datadir: Path) -> Generator[Path, None, None]:
    """A mocked directory with style files organised into "identify" subdirs."""
    with mock.patch("nitpick.style.builtin_resources_root") as mock_builtin_resources_root:
        mock_builtin_resources_root.return_value = Path(shared_datadir / "typed-style-dir")
        yield mock_builtin_resources_root


@pytest.mark.parametrize(
    ("pyproject_toml", "fix", "before", "after"),
    [
        (None, True, "", ""),
        ("", True, BLANK_LINE, ""),
        # Existing table with other keys
        (f"[{CONFIG_TOOL_NITPICK_KEY}]\nabc = 1", True, "", f"{BLANK_LINE}abc = 1"),
        # TODO(AA): test init when there is a [tool.nitpick] section but no [tool.nitpick.style] key
    ],
)
def test_create_update_tool_nitpick_table_on_config_files(
    style_dir_with_types: Path,
    tmp_path: Path,
    pyproject_toml: str | None,
    fix: bool,
    before: str,
    after: str,
) -> None:
    """If no config file is found, create a basic .nitpick.toml."""
    assert style_dir_with_types
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True)
    if pyproject_toml is None:
        config_file = DOT_NITPICK_TOML
    else:
        config_file = PYTHON_PYPROJECT_TOML
        project.pyproject_toml(pyproject_toml)
    project.cli_init(
        f"""
        New styles:
        - py://data/typed-style-dir/any/editorconfig
        - py://data/typed-style-dir/python/black
        The [{CONFIG_TOOL_NITPICK_KEY}] table was updated in {config_file!r}: 2 styles appended. {EmojiEnum.STAR_CAKE.value}
        """,
        fix=fix,
        suggest=True,
        exit_code=1 if fix else 0,
    )
    if fix:
        project.assert_file_contents(
            config_file,
            f"""
            {before}[{CONFIG_TOOL_NITPICK_KEY}]{after}
            # nitpick-start (auto-generated by "nitpick init --suggest" {__version__})
            # Styles added to the Nitpick Style Library will be appended at the end of the 'style' key.
            # If you don't want a style, move it to the 'dont_suggest' key.
            # nitpick-end
            style = [
              "py://data/typed-style-dir/any/editorconfig",
              "py://data/typed-style-dir/python/black",]
            dont_suggest = []
            """,
        )
    else:
        assert not (tmp_path / DOT_NITPICK_TOML).exists()


@pytest.mark.parametrize(
    ("styles", "expected_styles"),
    [
        ((), "style = ['py://nitpick/resources/presets/nitpick']"),  # no arguments, default style
        (
            ("https://github.com/andreoliwa/nitpick/blob/develop/initial.toml", "./local.toml"),
            "style = ['https://github.com/andreoliwa/nitpick/blob/develop/initial.toml', './local.toml']",
        ),
    ],
)
@pytest.mark.skip(reason="WIP")  # TODO(AA): fix the test
def test_add_tool_nitpick_section_to_pyproject_toml(tmp_path, styles, expected_styles) -> None:
    """Add a [tool.nitpick] section to pyproject.toml."""
    project = ProjectMock(tmp_path).pyproject_toml(
        """
        [tool.black]
        line-length = 120
        """
    )
    expected = styles or [StyleManager.get_default_style_url()]

    project.cli_init(
        f"The [{CONFIG_TOOL_NITPICK_KEY}] section was created in the config file {PYTHON_PYPROJECT_TOML!r}\n{expected_styles}",
        *styles,
    ).assert_file_contents(
        PYTHON_PYPROJECT_TOML,
        f"""
        [tool.black]
        line-length = 120

        [{CONFIG_TOOL_NITPICK_KEY}]
        # Generated by the 'nitpick init' command
        # More info at {READ_THE_DOCS_URL}configuration.html
        style = {tomlkit.array([tomlkit.string(str(url)) for url in expected]).as_string()}
        """,
    )


# TODO(AA): test create the ignored styles array only when suggesting styles
