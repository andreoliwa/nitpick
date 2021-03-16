"""Test cache."""
from datetime import timedelta

import pytest
from freezegun import freeze_time

from nitpick.enums import CachingEnum
from nitpick.style import parse_cache_option


@pytest.mark.tool_nitpick("cache = 'forever'")
def test_forever(project_remote):
    """Test cache being stored forever."""
    project_remote.assert_call_count(0)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    project_remote.assert_call_count(1)


@pytest.mark.tool_nitpick("cache = 'never'")
def test_never(project_remote):
    """Test cache being never stored."""
    project_remote.assert_call_count(0)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    project_remote.assert_call_count(3)


@pytest.mark.parametrize(
    "cache_option,expected_enum,expected_timedelta",
    [
        ("never", CachingEnum.NEVER, timedelta()),
        (" NEVER\n ", CachingEnum.NEVER, timedelta()),
        ("forever", CachingEnum.FOREVER, timedelta()),
        ("\t  Forever \n", CachingEnum.FOREVER, timedelta()),
        (" 15 minutes garbage", CachingEnum.EXPIRES, timedelta(minutes=15)),
        (" 20 minute ", CachingEnum.EXPIRES, timedelta(minutes=20)),
        (" 3 hours ", CachingEnum.EXPIRES, timedelta(hours=3)),
        (" 2 hour ", CachingEnum.EXPIRES, timedelta(hours=2)),
        (" 4 hourly whatever ", CachingEnum.EXPIRES, timedelta(hours=4)),
        (" 2 days ", CachingEnum.EXPIRES, timedelta(days=2)),
        (" 3 dayly bread ", CachingEnum.EXPIRES, timedelta(days=3)),
        (" 1 week ", CachingEnum.EXPIRES, timedelta(weeks=1)),
        (" 2 weeks ", CachingEnum.EXPIRES, timedelta(weeks=2)),
        ("", CachingEnum.EXPIRES, timedelta(hours=1)),
        ("   ", CachingEnum.EXPIRES, timedelta(hours=1)),
        (" 1 second ", CachingEnum.EXPIRES, timedelta(hours=1)),
        (" 2 bananas ", CachingEnum.EXPIRES, timedelta(hours=1)),
    ],
)
def test_parse_cache_option(cache_option, expected_enum, expected_timedelta):
    """Test the cache option provided on pyproject.toml.

    doctest-style failed on the GitHub Workflow because the timedelta output is different on Python 3.6 and 3.7:

    064     >>> parse_cache_option(" 15 minutes garbage")
    Expected:
      (<CachingEnum.EXPIRES: 3>, datetime.timedelta(0, 900))
    Got:
      (<CachingEnum.EXPIRES: 3>, datetime.timedelta(seconds=900))

    /home/runner/work/nitpick/nitpick/src/nitpick/style.py:64: DocTestFailure
    """
    assert parse_cache_option(cache_option) == (expected_enum, expected_timedelta)


@pytest.mark.tool_nitpick("cache = '15 minutes'")
def test_expiration(project_remote):
    """Test cache expiring after some time."""
    with freeze_time("2021-03-10 22:00") as frozen_datetime:
        project_remote.assert_call_count(0)

        # One HTTP request
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Still one request
        frozen_datetime.move_to("2021-03-10 22:13")
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Time's up: another HTTP request
        frozen_datetime.move_to("2021-03-10 22:16")
        project_remote.api_check().assert_violations().assert_call_count(2)


def test_default_cache_when_nothing_provided(project_remote):
    """Test the default cache option when nothing is provided: 1 hour."""
    with freeze_time("2021-03-16 11:00") as frozen_datetime:
        project_remote.assert_call_count(0)

        # One HTTP request
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Still one request
        frozen_datetime.move_to("2021-03-16 11:30")
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Time's up: another HTTP request
        frozen_datetime.move_to("2021-03-16 12:01")
        project_remote.api_check().assert_violations().assert_call_count(2)
