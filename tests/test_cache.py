"""Test caching styles."""
from textwrap import dedent

import responses

from tests.helpers import ProjectMock


@responses.activate
def test_forever(tmp_path):
    """Test cache being stored forever."""
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

    for _ in range(3):
        project.api_check().assert_violations()
    assert responses.assert_call_count(remote_url, 1)
