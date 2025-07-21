"""TOML files."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, ClassVar, Iterator, cast

from tomlkit import dumps, parse

from nitpick.blender import Comparison, TomlDoc, traverse_toml_tree
from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.violations import Fuss, SharedViolations, ViolationEnum

if TYPE_CHECKING:
    from tomlkit.toml_document import TOMLDocument

    from nitpick.plugins.info import FileInfo


class TomlPlugin(NitpickPlugin):
    """Enforce configurations and autofix TOML files.

    E.g.: `pyproject.toml (PEP 518) <https://www.python.org/dev/peps/pep-0518/#file-format>`_.

    See also `the [tool.poetry] section of the pyproject.toml file
    <https://github.com/python-poetry/poetry/blob/master/docs/pyproject.md>`_.

    Style example: :gitref:`Python 3.8 version constraint <src/nitpick/resources/python/38.toml>`.
    There are :ref:`many other examples here <library>`.
    """

    identify_tags: ClassVar = {"toml"}
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
            self.report(SharedViolations.DIFFERENT_VALUES, document, cast("TomlDoc", comparison.diff)),
            self.report(
                SharedViolations.MISSING_VALUES,
                document,
                cast("TomlDoc", comparison.missing),
                cast("TomlDoc", comparison.replace),
            ),
        )
        if self.autofix and self.dirty:
            self.file_path.write_text(dumps(document))

    def report(
        self,
        violation: ViolationEnum,
        document: TOMLDocument | None,
        change: TomlDoc | None,
        replacement: TomlDoc | None = None,
    ):
        """Report a violation while optionally modifying the TOML document."""
        if not (change or replacement):
            return
        if self.autofix:
            real_change = cast("TomlDoc", replacement or change)
            traverse_toml_tree(document, real_change.as_object)
            self.dirty = True

        to_display = cast("TomlDoc", change or replacement)
        yield self.reporter.make_fuss(violation, to_display.reformatted.strip(), prefix="", fixed=self.autofix)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.write_initial_contents(TomlDoc)


@hookimpl
def plugin_class() -> type[NitpickPlugin]:
    """Handle TOML files."""
    return TomlPlugin


@hookimpl
def can_handle(info: FileInfo) -> type[NitpickPlugin] | None:
    """Handle TOML files."""
    if TomlPlugin.identify_tags & info.tags:
        return TomlPlugin
    return None
