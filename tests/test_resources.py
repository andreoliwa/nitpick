"""Resource tests."""
from pathlib import Path

from identify.identify import ALL_TAGS

from tests.helpers import STYLES_DIR


def test_packages_named_after_identify_tags():
    """Test if the directories are packages and also "identify" tags."""
    for item in Path(STYLES_DIR).glob("**/*"):
        if not item.is_dir() or item.name in {"__pycache__", "any"}:
            continue

        assert item.name in ALL_TAGS, f"The directory {item.name!r} is not a valid 'identify' tag"
        init_py = list(item.glob("__init__.py"))
        assert init_py, f"The directory {item.name!r} is not a Python package"
        assert init_py[0].is_file()
