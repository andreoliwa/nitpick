"""Resource tests."""
from pathlib import Path
from typing import Dict, List

import pytest
from icecream import ic
from identify.identify import ALL_TAGS

from nitpick.constants import (
    DOT_NITPICK_TOML,
    EDITOR_CONFIG,
    PACKAGE_JSON,
    PRE_COMMIT_CONFIG_YAML,
    PYLINTRC,
    PYPROJECT_TOML,
    SETUP_CFG,
    TOX_INI,
)
from nitpick.style.fetchers.pypackage import BuiltinStyle, builtin_styles
from nitpick.violations import Fuss
from tests.helpers import STYLES_DIR, ProjectMock

BUILTIN_STYLE_CODES = {
    SETUP_CFG: 321,
    PRE_COMMIT_CONFIG_YAML: 361,
    PYPROJECT_TOML: 311,
    ".codeclimate.yml": 361,
    ".readthedocs.yml": 361,
    TOX_INI: 321,
    PYLINTRC: 321,
    ".github/workflows/python.yaml": 361,
    EDITOR_CONFIG: 321,
    PACKAGE_JSON: 341,
}
BUILTIN_STYLE_EXTRA_VIOLATIONS: Dict[str, List[Fuss]] = {
    "any/pre-commit-hooks": [
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            103,
            " should exist: Create the file with the contents below, then run 'pre-commit install'",
            "",
        )
    ],
    "python/poetry": [
        Fuss(False, PYPROJECT_TOML, 103, " should exist: Install poetry and run 'poetry init' to create it", "")
    ],
}


def test_packages_named_after_identify_tags():
    """Test if the directories are packages and also "identify" tags."""
    for item in Path(STYLES_DIR).glob("**/*"):
        if not item.is_dir() or item.name in {"__pycache__", "any"}:
            continue

        assert item.name in ALL_TAGS, f"The directory {item.name!r} is not a valid 'identify' tag"
        init_py = list(item.glob("__init__.py"))
        assert init_py, f"The directory {item.name!r} is not a Python package"
        assert init_py[0].is_file()


@pytest.mark.parametrize("builtin_style_path", builtin_styles())
def test_each_builtin_style(tmp_path, datadir, builtin_style_path):
    """Test each built-in style."""
    style = BuiltinStyle.from_path(builtin_style_path)
    violations = []
    name_contents = []
    for filename in style.files:
        expected_path = datadir / style.path_from_resources_root / filename
        if not expected_path.exists():
            fixture_path = Path(__file__).parent / "test_resources" / style.path_from_resources_root / filename
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.touch(exist_ok=True)

        expected_contents = expected_path.read_text()
        code = BUILTIN_STYLE_CODES[filename]
        violations.append(Fuss(True, filename, code, " was not found. Create it with this content:", expected_contents))
        name_contents.extend([filename, expected_contents])

    ic(style.path_from_resources_root)
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
