"""Test built-in styles shipped as resources under the ``nitpick.resources`` module."""
from __future__ import annotations

from pathlib import Path

import pytest
from identify.identify import ALL_TAGS

from nitpick.constants import (
    DOT_NITPICK_TOML,
    EDITOR_CONFIG,
    JAVASCRIPT_PACKAGE_JSON,
    PRE_COMMIT_CONFIG_YAML,
    PYTHON_POETRY_TOML,
    PYTHON_PYLINTRC,
    PYTHON_PYPROJECT_TOML,
    PYTHON_SETUP_CFG,
    PYTHON_TOX_INI,
)
from nitpick.style import BuiltinStyle, builtin_styles
from nitpick.violations import Fuss
from tests.helpers import STYLES_DIR, ProjectMock

RESOURCES_DIR = Path(__file__).parent.parent / "src/nitpick/resources"
BUILTIN_STYLE_CODES = {
    # keep-sorted start
    ".codeclimate.yml": 361,
    ".github/workflows/python.yaml": 361,
    ".readthedocs.yaml": 361,
    EDITOR_CONFIG: 321,
    JAVASCRIPT_PACKAGE_JSON: 341,
    PRE_COMMIT_CONFIG_YAML: 361,
    PYTHON_POETRY_TOML: 311,
    PYTHON_PYLINTRC: 321,
    PYTHON_PYPROJECT_TOML: 311,
    PYTHON_SETUP_CFG: 321,
    PYTHON_TOX_INI: 321,
    # keep-sorted end
}
BUILTIN_STYLE_EXTRA_VIOLATIONS: dict[str, list[Fuss]] = {
    "any/pre-commit-hooks": [
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            103,
            " should exist: Create the file with the contents below, then run 'pre-commit install'",
            "",
        )
    ],
}


def test_packages_named_after_identify_tags():
    """Test if the directories are packages and also "identify" tags."""
    for item in Path(STYLES_DIR).glob("**/*"):
        if not item.is_dir() or item.name in {"__pycache__", "any", "presets"}:
            continue

        assert item.name in ALL_TAGS, f"The directory {item.name!r} is not a valid 'identify' tag"
        init_py = list(item.glob("__init__.py"))
        assert init_py, f"The directory {item.name!r} is not a Python package"
        assert init_py[0].is_file()


@pytest.mark.parametrize(
    "relative_path",
    sorted(str(s.relative_to(RESOURCES_DIR)) for s in builtin_styles() if "presets" not in s.parts),
)
def test_each_builtin_style(tmp_path, datadir, relative_path):
    """Test each built-in style (skip presets)."""
    style = BuiltinStyle.from_path(RESOURCES_DIR / relative_path)
    violations = []
    name_contents = []
    for filename in style.files:
        expected_path = datadir / style.path_from_resources_root / filename

        if not expected_path.exists():
            # Creates empty files on datadir, to help with the task of adding new built-in styles
            # You just need to fill in the expected contents of each file
            fixture_path = Path(__file__).parent / "test_builtin" / style.path_from_resources_root / filename
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.touch(exist_ok=True)

        expected_contents = expected_path.read_text()
        code = BUILTIN_STYLE_CODES[filename]
        violations.append(Fuss(True, filename, code, " was not found. Create it with this content:", expected_contents))
        name_contents.extend([filename, expected_contents])

    violations.extend(BUILTIN_STYLE_EXTRA_VIOLATIONS.get(style.path_from_resources_root, []))

    project = ProjectMock(tmp_path).save_file(
        DOT_NITPICK_TOML,
        f"""
        [tool.nitpick]
        style = "{style.py_url_without_ext}"
        """,
    )

    # Run `nitpick fix` twice on the style
    # First time check: it should report violations and create new file(s)
    project.api_check_then_fix(*violations)
    if style.files:
        project.assert_file_contents(*name_contents)

    has_unfixed_violations = any(not fuss.fixed for fuss in violations)
    if has_unfixed_violations:
        # If some violations can't be fixed, we can't check for the second time and we must leave
        return

    # Second time check: it should not report any violation and should not change the existing file(s)
    project.api_check_then_fix()
    if style.files:
        project.assert_file_contents(*name_contents)
    # TODO: test: special case for src/nitpick/resources/python/absent.toml


def test_default_style_is_applied(project_default, datadir):
    """Test if the default style is applied on an empty project."""
    # TODO: test: nitpick preset in a generic way, preparing for other presets to come
    preset_dir = datadir / "preset" / "nitpick"
    expected_setup_cfg = (preset_dir / "setup.cfg").read_text()
    expected_editor_config = (preset_dir / ".editorconfig").read_text()
    expected_tox_ini = (preset_dir / "tox.ini").read_text()
    expected_pylintrc = (preset_dir / ".pylintrc").read_text()
    project_default.api_check_then_fix(
        Fuss(True, PYTHON_SETUP_CFG, 321, " was not found. Create it with this content:", expected_setup_cfg),
        Fuss(True, EDITOR_CONFIG, 321, " was not found. Create it with this content:", expected_editor_config),
        Fuss(True, PYTHON_TOX_INI, 321, " was not found. Create it with this content:", expected_tox_ini),
        Fuss(True, PYTHON_PYLINTRC, 321, " was not found. Create it with this content:", expected_pylintrc),
        partial_names=[PYTHON_SETUP_CFG, EDITOR_CONFIG, PYTHON_TOX_INI, PYTHON_PYLINTRC],
    ).assert_file_contents(
        PYTHON_SETUP_CFG,
        expected_setup_cfg,
        EDITOR_CONFIG,
        expected_editor_config,
        PYTHON_TOX_INI,
        expected_tox_ini,
        PYTHON_PYLINTRC,
        expected_pylintrc,
    )


def test_pre_commit_with_multiple_repos_should_not_change_if_repos_exist(tmp_path, datadir):
    """A real pre-commit config with multiple repos should not be changed if all the expected repos are there.

    This test belongs to ``test_builtin.py`` because "real.toml" has references to built-in styles.
    """
    ProjectMock(tmp_path).save_file(PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml").style(
        datadir / "real.toml"
    ).api_check_then_fix(partial_names=[PRE_COMMIT_CONFIG_YAML]).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "real.yaml"
    ).api_check(
        PRE_COMMIT_CONFIG_YAML
    ).assert_violations()
