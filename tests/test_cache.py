"""Test cache."""
from textwrap import dedent

import pytest
import responses

from nitpick.enums import CachingEnum
from tests.helpers import ProjectMock


@responses.activate
@pytest.mark.parametrize("caching,expected_request_count", [(CachingEnum.FOREVER, 1), (CachingEnum.NEVER, 3)])
def test_forever_never(caching, expected_request_count, tmp_path):
    """Test cache being stored forever and never."""
    remote_url = "https://example.com/remote-style.toml"
    remote_style = """
        ["pyproject.toml".tool.black]
        line-length = 100
    """
    responses.add(responses.GET, remote_url, dedent(remote_style), status=200)

    project = ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "{remote_url}"

        [tool.black]
        line-length = 100
        """
    )
    assert responses.assert_call_count(remote_url, 0)

    project.cache(caching)
    for _ in range(3):
        project.api_check().assert_violations()
    assert responses.assert_call_count(remote_url, expected_request_count)
