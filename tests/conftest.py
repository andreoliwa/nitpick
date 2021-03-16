"""Pytest fixtures."""
from pathlib import Path
from textwrap import dedent

import pytest
from responses import RequestsMock


@pytest.fixture()
def project_default(tmp_path):
    """Project with the default Nitpick style.

    These imports below have to be here within the fixture, otherwise they raise an error on tox:

        $ tox -e clean,py38,report
        (...)
        Coverage.py warning: No data was collected. (no-data-collected)
        .tox/py38/lib/python3.8/site-packages/pytest_cov/plugin.py:271:
         PytestWarning: Failed to generate report: No data to report.
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


@pytest.fixture()
def project_remote(request, tmp_path):
    """Project with a remote style (loaded from a URL)."""
    from tests.helpers import ProjectMock

    remote_url = "https://example.com/remote-style.toml"
    remote_style = """
        ["pyproject.toml".tool.black]
        line-length = 100
    """
    # https://docs.pytest.org/en/stable/fixture.html#using-markers-to-pass-data-to-fixtures
    marker = request.node.get_closest_marker("tool_nitpick")
    tool_nitpick = marker.args[0] if marker else ""

    with RequestsMock() as mocked_response:
        mocked_response.add(mocked_response.GET, remote_url, dedent(remote_style), status=200)

        project = ProjectMock(tmp_path)
        project.pyproject_toml(
            f"""
            [tool.nitpick]
            style = "{remote_url}"
            {tool_nitpick}

            [tool.black]
            line-length = 100
            """
        ).remote(mocked_response, remote_url)
        yield project
