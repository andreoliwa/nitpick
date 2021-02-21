"""Pytest fixtures."""
from pathlib import Path

import pytest


@pytest.fixture()
def project_with_default_style(tmp_path):
    """Project with the default Nitpick style.

    .. note::

        These imports below have to be here. within the fixture, otherwise they raise an error on tox:

        $ tox -e clean,py38,report
        (...)
        Coverage.py warning: No data was collected. (no-data-collected)
        .tox/py38/lib/python3.8/site-packages/pytest_cov/plugin.py:271: PytestWarning:
            Failed to generate report: No data to report.
    """
    from nitpick.constants import NITPICK_STYLE_TOML
    from tests.helpers import ProjectMock

    nitpick_style = Path(__file__).parent.parent / NITPICK_STYLE_TOML
    return ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "{nitpick_style}"
        """
    )
