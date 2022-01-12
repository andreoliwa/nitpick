"""TOML files."""
from itertools import chain
from typing import Iterator, Optional, Type

from tomlkit import dumps, parse
from tomlkit.toml_document import TOMLDocument

from nitpick.blender import BaseDoc, Comparison, TomlDoc, traverse_toml_tree
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.violations import Fuss, SharedViolations, ViolationEnum


class TomlPlugin(NitpickPlugin):
    """Enforce configurations and autofix TOML files.

    E.g.: `pyproject.toml (PEP 518) <https://www.python.org/dev/peps/pep-0518/#file-format>`_.

    See also `the [tool.poetry] section of the pyproject.toml file
    <https://github.com/python-poetry/poetry/blob/master/docs/pyproject.md>`_.

    Style example: :ref:`Python 3.8 version constraint <example-python-3-8>`.
    There are :ref:`many other examples here <examples>`.
    """

    identify_tags = {"toml"}
    violation_base_code = 310
    fixable = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing key/value pairs in the TOML file."""
        toml_doc = TomlDoc(path=self.file_path)
        comparison = Comparison(toml_doc, self.expected_config, self.special_config)()
        if not comparison.has_changes:
            return

        document = parse(toml_doc.as_string) if self.autofix else None
        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, document, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, document, comparison.missing),
        )
        if self.autofix and self.dirty:
            self.file_path.write_text(dumps(document))

    def report(self, violation: ViolationEnum, document: Optional[TOMLDocument], change: Optional[BaseDoc]):
        """Report a violation while optionally modifying the TOML document."""
        if not change:
            return
        if document:
            traverse_toml_tree(document, change.as_object)
            self.dirty = True
        yield self.reporter.make_fuss(violation, change.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.write_initial_contents(TomlDoc)


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
