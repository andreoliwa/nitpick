"""Cache functions and configuration for styles."""
from __future__ import annotations

import re
from datetime import timedelta

from loguru import logger
from requests_cache.cache_control import DO_NOT_CACHE, NEVER_EXPIRE

from nitpick.enums import CachingEnum

REGEX_CACHE_UNIT = re.compile(r"(?P<number>\d+)\s+(?P<unit>(minute|hour|day|week))", re.IGNORECASE)
EXPIRES_DEFAULTS = {
    CachingEnum.NEVER: DO_NOT_CACHE,
    CachingEnum.FOREVER: NEVER_EXPIRE,
    CachingEnum.EXPIRES: timedelta(hours=1),
}


def parse_cache_option(cache_option: str) -> tuple[CachingEnum, timedelta | int]:
    """Parse the cache option provided on pyproject.toml.

    If no cache if provided or is invalid, the default is *one hour*.

    """
    clean_cache_option = cache_option.strip().upper() if cache_option else ""
    try:
        caching = CachingEnum[clean_cache_option]
        logger.info(f"Simple cache option: {caching.name}")
    except KeyError:
        caching = CachingEnum.EXPIRES

    expires_after = EXPIRES_DEFAULTS[caching]
    if caching is CachingEnum.EXPIRES and clean_cache_option:
        for match in REGEX_CACHE_UNIT.finditer(clean_cache_option):
            plural_unit = match.group("unit").lower() + "s"
            number = int(match.group("number"))
            logger.info(f"Cache option with unit: {number} {plural_unit}")
            expires_after = timedelta(**{plural_unit: number})
            break
        else:
            logger.warning(f"Invalid cache option: {clean_cache_option}. Defaulting to 1 hour")

    return caching, expires_after
