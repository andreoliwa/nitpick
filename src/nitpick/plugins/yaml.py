"""YAML files."""
from itertools import chain
from typing import Iterator, Optional, Type

from ruamel.yaml import YAML

from nitpick.constants import PRE_COMMIT_CONFIG_YAML
from nitpick.formats import BaseFormat, YamlFormat
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.plugins.text import KEY_CONTAINS
from nitpick.typedefs import YamlObject
from nitpick.violations import Fuss, SharedViolations, ViolationEnum


def change_yaml(document: YAML, dictionary: YamlObject):
    """Traverse a YAML document recursively and change values, keeping its formatting and comments."""
    del document
    del dictionary
    # FIXME:
    # for key, value in dictionary.items():
    #     if isinstance(value, (dict, OrderedDict)):
    #         if key in document:
    #             change_toml(document[key], value)
    #         else:
    #             document.add(key, value)
    #     else:
    #         document[key] = value


class YamlPlugin(NitpickPlugin):
    """Enforce config on YAML files."""

    identify_tags = {"yaml"}
    violation_base_code = 360
    fixable = False  # FIXME:

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

        document = yaml_format.document if self.autofix else None
        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, document, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, document, comparison.missing),
        )
        if self.autofix and self.dirty and document:
            document.dump(document, self.file_path)

    def report(self, violation: ViolationEnum, document: Optional[YAML], change: Optional[BaseFormat]):
        """Report a violation while optionally modifying the YAML document."""
        if not change:
            return
        if document:
            change_yaml(document, change.as_object)
            self.dirty = True
        yield self.reporter.make_fuss(violation, change.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        yaml_as_string = YamlFormat(obj=self.expected_config).reformatted
        if self.autofix:
            self.file_path.write_text(yaml_as_string)
        return yaml_as_string


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
