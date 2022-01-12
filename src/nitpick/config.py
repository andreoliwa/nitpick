"""Special configurations."""
from attrs import Factory, define

from nitpick.typedefs import JsonDict


@define
class OverridableConfig:  # pylint: disable=too-few-public-methods
    """Configs formed from defaults from the plugin that can be overridden by the style."""

    from_plugin: JsonDict
    from_style: JsonDict = Factory(dict)
    value: JsonDict = Factory(dict)


@define
class SpecialConfig:  # pylint: disable=too-few-public-methods
    """Special configurations for plugins."""

    list_keys: OverridableConfig
