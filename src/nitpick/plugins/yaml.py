"""YAML files."""
from collections import OrderedDict
from itertools import chain
from typing import Iterator, List, Optional, Type, Union

from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.formats import BaseFormat, YamlFormat
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.plugins.text import KEY_CONTAINS
from nitpick.typedefs import JsonDict, YamlObject, YamlValue
from nitpick.violations import Fuss, SharedViolations, ViolationEnum


def is_scalar(value: YamlValue) -> bool:
    """Return True if the value is NOT a dict or a list."""
    return not isinstance(value, (OrderedDict, list))


def traverse_yaml_tree(yaml_obj: YamlObject, change: Union[JsonDict, OrderedDict]):
    """Traverse a YAML document recursively and change values, keeping its formatting and comments."""
    for key, value in change.items():
        if key not in yaml_obj:
            # Key doesn't exist: we can insert the whole nested OrderedDict at once, no regrets
            last_pos = len(yaml_obj.keys()) + 1
            yaml_obj.insert(last_pos, key, value)
            continue

        if is_scalar(value):
            yaml_obj[key] = value
        elif isinstance(value, OrderedDict):
            traverse_yaml_tree(yaml_obj[key], value)
        elif isinstance(value, list):
            _traverse_yaml_list(yaml_obj, key, value)


def _traverse_yaml_list(yaml_obj: YamlObject, key: str, value: List[YamlValue]):
    for index, element in enumerate(value):
        insert: bool = index >= len(yaml_obj[key])

        if not insert and is_scalar(yaml_obj[key][index]):
            # If the original object is scalar, replace it with whatever element;
            # without traversing, even if it's a dict
            yaml_obj[key][index] = element
            continue

        if is_scalar(element):
            if insert:
                yaml_obj[key].append(element)
            else:
                yaml_obj[key][index] = element
            continue

        traverse_yaml_tree(yaml_obj[key][index], element)  # type: ignore # mypy kept complaining about the Union


class YamlPlugin(NitpickPlugin):
    """Enforce configurations and autofix YAML files."""

    identify_tags = {"yaml"}
    violation_base_code = 360
    fixable = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing data in the YAML file."""
        if KEY_CONTAINS in self.expected_config:
            # If the expected configuration has this key, it means that this config is being handled by TextPlugin.
            # TODO: A YAML file that has a "contains" key on its root cannot be handled as YAML... how to fix this?
            return

        yaml_format = YamlFormat(path=self.file_path)
        comparison = yaml_format.compare_with_flatten(self.expected_config)
        if not comparison.has_changes:
            return

        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, yaml_format.as_object, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, yaml_format.as_object, comparison.missing),
        )
        if self.autofix and self.dirty:
            yaml_format.document.dump(yaml_format.as_object, self.file_path)

    def report(self, violation: ViolationEnum, yaml_object: YamlObject, change: Optional[BaseFormat]):
        """Report a violation while optionally modifying the YAML document."""
        if not change:
            return
        if self.autofix:
            traverse_yaml_tree(yaml_object, change.as_object)
            self.dirty = True
        yield self.reporter.make_fuss(violation, change.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.write_initial_contents(YamlFormat)


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """Handle YAML files."""
    return YamlPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle YAML files."""
    if info.path_from_root == PRE_COMMIT_CONFIG_YAML:
        # TODO: For now, this plugin won't touch the current pre-commit config
        return None

    if YamlPlugin.identify_tags & info.tags:
        return YamlPlugin
    return None
