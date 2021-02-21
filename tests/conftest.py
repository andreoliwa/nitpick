"""Pytest fixtures."""
from pathlib import Path

import pytest

from nitpick.constants import NITPICK_STYLE_TOML
from tests.helpers import ProjectMock


@pytest.fixture()
def project_with_default_style(tmp_path) -> ProjectMock:
    """Project with the default Nitpick style."""
    nitpick_style = Path(__file__).parent.parent / NITPICK_STYLE_TOML
    return ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "{nitpick_style}"
        """
    )
