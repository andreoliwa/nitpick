"""TOML files."""
from collections import OrderedDict
from itertools import chain
from typing import Iterator, Optional, Type

from tomlkit import dumps, parse
from tomlkit.toml_document import TOMLDocument

from nitpick.formats import BaseFormat, TOMLFormat
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.violations import Fuss, SharedViolations, ViolationEnum


def change_toml(document: TOMLDocument, dictionary):
    """Traverse a TOML document recursively and change values, keeping its formatting and comments."""
    for key, value in dictionary.items():
        if isinstance(value, (dict, OrderedDict)):
            if key in document:
                change_toml(document[key], value)
            else:
                document.add(key, value)
        else:
            document[key] = value


class TomlPlugin(NitpickPlugin):
    """Enforce config on TOML files.

    E.g.: `pyproject.toml (PEP 518) <https://www.python.org/dev/peps/pep-0518/#file-format>`_.

    See also `the [tool.poetry] section of the pyproject.toml file
    <https://github.com/python-poetry/poetry/blob/master/docs/pyproject.md>`_.

    Style example: :ref:`Python 3.8 version constraint <example-python-3-8>`.
    There are :ref:`many other examples here <examples>`.
    """

    identify_tags = {"toml"}
    violation_base_code = 310
    can_fix = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing key/value pairs in the TOML file."""
        toml_format = TOMLFormat(path=self.file_path)
        comparison = toml_format.compare_with_flatten(self.expected_config)
        if not comparison.has_changes:
            return

        document = parse(toml_format.as_string) if self.fix else None
        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, document, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, document, comparison.missing),
        )
        if self.fix and self.dirty:
            self.file_path.write_text(dumps(document))

    def report(self, violation: ViolationEnum, document: Optional[TOMLDocument], change_dict: Optional[BaseFormat]):
        """Report a violation while optionally modifying the TOML document."""
        if not change_dict:
            return
        if document:
            change_toml(document, change_dict.as_data)
            self.dirty = True
        yield self.reporter.make_fuss(violation, change_dict.reformatted.strip(), prefix="", fixed=self.fix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        rv = TOMLFormat(data=self.expected_config).reformatted
        if self.fix:
            self.file_path.write_text(rv)
        return rv


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """Handle TOML files."""
    return TomlPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle TOML files."""
    if TomlPlugin.identify_tags & info.tags:
        return TomlPlugin
    return None
