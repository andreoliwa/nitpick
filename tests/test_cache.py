"""Test cache."""
import pytest

from nitpick.enums import CachingEnum


@pytest.mark.parametrize("caching,expected_request_count", [(CachingEnum.FOREVER, 1), (CachingEnum.NEVER, 3)])
def test_forever_never(caching, expected_request_count, project_remote):
    """Test cache being stored forever and never."""
    project_remote.assert_call_count(0)

    project_remote.cache(caching)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    assert project_remote.assert_call_count(expected_request_count)


# FIXME[AA]: with freeze_time("2012-01-14"):
