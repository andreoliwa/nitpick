"""Enforce config on `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_."""
from collections import OrderedDict
from itertools import chain
from typing import Iterator, Optional, Type

from tomlkit import dumps, parse
from tomlkit.toml_document import TOMLDocument

from nitpick.constants import PYPROJECT_TOML
from nitpick.core import Nitpick
from nitpick.formats import BaseFormat
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


class PyProjectTomlPlugin(NitpickPlugin):
    """Enforce config on `pyproject.toml <https://github.com/python-poetry/poetry/blob/master/docs/docs/pyproject.md>`_.

    See also `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_.

    Example: :ref:`the Python 3.7 default <default-python-3-7>`.
    There are many other examples in :ref:`defaults`.
    """

    filename = PYPROJECT_TOML
    violation_base_code = 310
    can_apply = True

    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules for missing key/value pairs in pyproject.toml."""
        file = Nitpick.singleton().project.pyproject_toml
        if not file:
            return

        comparison = file.compare_with_flatten(self.expected_config)
        if not comparison.has_changes:
            return

        document = parse(file.as_string) if self.apply else None
        yield from chain(
            self.report(SharedViolations.DIFFERENT_VALUES, document, comparison.diff),
            self.report(SharedViolations.MISSING_VALUES, document, comparison.missing),
        )
        if self.apply:
            self.file_path.write_text(dumps(document))

    def report(self, violation: ViolationEnum, document: Optional[TOMLDocument], change_dict: Optional[BaseFormat]):
        """Report a violation while optionally applying it to the TOML document."""
        if not change_dict:
            return
        if document:
            change_toml(document, change_dict.as_data)
        yield self.reporter.make_fuss(violation, change_dict.reformatted.strip(), prefix="", fixed=self.apply)

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return ""


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return PyProjectTomlPlugin


@hookimpl
def can_handle(info: FileInfo) -> Optional[Type["NitpickPlugin"]]:
    """Handle pyproject.toml file."""
    if info.path_from_root == PYPROJECT_TOML:
        return PyProjectTomlPlugin
    return None
