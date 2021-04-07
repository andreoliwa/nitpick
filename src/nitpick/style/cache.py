"""Cache functions and configuration for styles."""
import re
from datetime import timedelta
from typing import Tuple

from loguru import logger

from nitpick.enums import CachingEnum

REGEX_CACHE_UNIT = re.compile(r"(?P<number>\d+)\s+(?P<unit>(minute|hour|day|week))", re.IGNORECASE)


def parse_cache_option(cache_option: str) -> Tuple[CachingEnum, timedelta]:
    """Parse the cache option provided on pyproject.toml.

    If no cache if provided or is invalid, the default is *one hour*.
    """
    clean_cache_option = cache_option.strip().lower() if cache_option else ""
    mapping = {CachingEnum.NEVER.name.lower(): CachingEnum.NEVER, CachingEnum.FOREVER.name.lower(): CachingEnum.FOREVER}
    simple_cache = mapping.get(clean_cache_option)
    if simple_cache:
        logger.info(f"Simple cache option: {simple_cache.name}")
        return simple_cache, timedelta()

    default = CachingEnum.EXPIRES, timedelta(hours=1)
    if not clean_cache_option:
        return default

    for match in REGEX_CACHE_UNIT.finditer(clean_cache_option):
        plural_unit = match.group("unit") + "s"
        number = int(match.group("number"))
        logger.info(f"Cache option with unit: {number} {plural_unit}")
        return CachingEnum.EXPIRES, timedelta(**{plural_unit: number})

    logger.warning(f"Invalid cache option: {clean_cache_option}. Defaulting to 1 hour")
    return default
