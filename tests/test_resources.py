"""Resource tests."""
from pathlib import Path

import pytest
from identify.identify import ALL_TAGS

from nitpick.constants import DOT_NITPICK_TOML, PRE_COMMIT_CONFIG_YAML, PYLINTRC, PYPROJECT_TOML, SETUP_CFG, TOX_INI
from nitpick.style.fetchers.pypackage import BuiltinStyle, builtin_styles
from nitpick.violations import Fuss
from tests.helpers import STYLES_DIR, ProjectMock

FUSS_CODE_MAPPING = {
    SETUP_CFG: 321,
    PRE_COMMIT_CONFIG_YAML: 361,
    PYPROJECT_TOML: 311,
    ".codeclimate.yml": 361,
    ".readthedocs.yml": 361,
    TOX_INI: 321,
    PYLINTRC: 321,
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


@pytest.mark.parametrize("path", list(builtin_styles())[:13])  # FIXME: test: all styles
def test_each_builtin_style(tmp_path, datadir, path):
    """Test each built-in style."""
    style = BuiltinStyle.from_path(path)
    fusses = []
    name_contents = []
    for filename in style.files:
        expected_path = datadir / style.path_from_resources_root / filename
        if not expected_path.exists():
            fixture_path = Path(__file__).parent / "test_resources" / style.path_from_resources_root / filename
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.touch(exist_ok=True)

        expected_contents = expected_path.read_text()
        code = FUSS_CODE_MAPPING[filename]
        fusses.append(Fuss(True, filename, code, " was not found. Create it with this content:", expected_contents))
        name_contents.extend([filename, expected_contents])

    project = ProjectMock(tmp_path).save_file(
        DOT_NITPICK_TOML,
        f"""
        [tool.nitpick]
        style = "{style.py_url_without_ext}"
        """,
    )
    project.api_check_then_fix(*fusses)
    if style.files:
        project.assert_file_contents(*name_contents)
    # TODO: test: special case for src/nitpick/resources/python/absent.toml
