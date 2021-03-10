"""Test cache."""
from datetime import timedelta

import pytest
from freezegun import freeze_time

from nitpick.enums import CachingEnum


@pytest.mark.parametrize("caching,expected_request_count", [(CachingEnum.FOREVER, 1), (CachingEnum.NEVER, 3)])
def test_forever_never(caching, expected_request_count, project_remote):
    """Test cache being stored forever and never."""
    project_remote.assert_call_count(0)

    project_remote.cache(caching)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    project_remote.assert_call_count(expected_request_count)


def test_expiration(project_remote):
    """Test cache expiring after some time."""
    with freeze_time("2021-03-10 22:00") as frozen_datetime:
        project_remote.assert_call_count(0).cache(CachingEnum.EXPIRES, timedelta(minutes=15))

        # One HTTP request
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Still one request
        frozen_datetime.move_to("2021-03-10 22:13")
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Time's up: another HTTP request
        frozen_datetime.move_to("2021-03-10 22:16")
        project_remote.api_check().assert_violations().assert_call_count(2)
