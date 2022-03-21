"""INI files."""
from __future__ import annotations

from configparser import ConfigParser, DuplicateOptionError, Error, MissingSectionHeaderError, ParsingError
from io import StringIO
from typing import Any, Iterator

import dictdiffer
from configupdater import ConfigUpdater, Space

from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.plugins.info import FileInfo
from nitpick.violations import Fuss, ViolationEnum

COMMA_SEPARATED_VALUES = "comma_separated_values"
SECTION_SEPARATOR = "."
TOP_SECTION = "__TEMPORARY_TOP_SECTION__"


class Violations(ViolationEnum):
    """Violations for this plugin."""

    MISSING_SECTIONS = (321, " has some missing sections. Use this:")
    MISSING_VALUES_IN_LIST = (322, " has missing values in the {key!r} key. Include those values:")
    OPTION_HAS_DIFFERENT_VALUE = (323, ": [{section}]{key} is {actual} but it should be like this:")
    MISSING_OPTION = (324, ": section [{section}] has some missing key/value pairs. Use this:")
    INVALID_COMMA_SEPARATED_VALUES_SECTION = (325, f": invalid sections on {COMMA_SEPARATED_VALUES}:")
    PARSING_ERROR = (326, ": parsing error ({cls}): {msg}")
    TOP_SECTION_HAS_DIFFERENT_VALUE = (327, ": {key} is {actual} but it should be:")
    TOP_SECTION_MISSING_OPTION = (328, ": top section has missing options. Use this:")


class IniPlugin(NitpickPlugin):
    """Enforce configurations and autofix INI files.

    Examples of ``.ini`` files handled by this plugin:

    - `setup.cfg <https://docs.python.org/3/distutils/configfile.html>`_
    - `.editorconfig <https://editorconfig.org/>`_
    - `tox.ini <https://github.com/tox-dev/tox>`_
    - `.pylintrc <https://pylint.readthedocs.io/en/latest/user_guide/run.html#command-line-options>`_

    Style examples enforcing values on INI files: :gitref:`flake8 configuration
    <src/nitpick/resources/python/flake8.toml>`.
    """

    fixable = True
    identify_tags = {"ini", "editorconfig"}
    violation_base_code = 320

    updater: ConfigUpdater
    comma_separated_values: set[str]

    def post_init(self):
        """Post initialization after the instance was created."""
        self.updater = ConfigUpdater()
        self.comma_separated_values = set(self.nitpick_file_dict.get(COMMA_SEPARATED_VALUES, []))

        if not self.needs_top_section:
            return
        if all(isinstance(v, dict) for v in self.expected_config.values()):
            return

        new_config = dict({TOP_SECTION: {}})
        for key, value in self.expected_config.items():
            if isinstance(value, dict):
                new_config[key] = value
                continue
            new_config[TOP_SECTION][key] = value
        self.expected_config = new_config

    @property
    def needs_top_section(self) -> bool:
        """Return True if this .ini file needs a top section (e.g.: .editorconfig)."""
        return "editorconfig" in self.info.tags

    @property
    def current_sections(self) -> set[str]:
        """Current sections of the .ini file, including updated sections."""
        return set(self.updater.sections())

    @property
    def initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.get_missing_output()

    @property
    def expected_sections(self) -> set[str]:
        """Expected sections (from the style config)."""
        return set(self.expected_config.keys())

    @property
    def missing_sections(self) -> set[str]:
        """Missing sections."""
        return self.expected_sections - self.current_sections

    def write_file(self, file_exists: bool) -> Fuss | None:
        """Write the new file."""
        try:
            if self.needs_top_section:
                self.file_path.write_text(self.contents_without_top_section(str(self.updater)))
                return None

            if file_exists:
                self.updater.update_file()
            else:
                self.updater.write(self.file_path.open("w"))
        except ParsingError as err:
            return self.reporter.make_fuss(Violations.PARSING_ERROR, cls=err.__class__.__name__, msg=err)
        return None

    @staticmethod
    def contents_without_top_section(multiline_text: str) -> str:
        """Remove the temporary top section from multiline text, and keep the newline at the end of the file."""
        return "\n".join(line for line in multiline_text.splitlines() if TOP_SECTION not in line) + "\n"

    def get_missing_output(self) -> str:
        """Get a missing output string example from the missing sections in an INI file."""
        missing = self.missing_sections
        if not missing:
            return ""

        parser = ConfigParser()
        for section in sorted(missing, key=lambda s: "0" if s == TOP_SECTION else f"1{s}"):
            expected_config: dict = self.expected_config[section]
            if self.autofix:
                if self.updater.last_block:
                    self.updater.last_block.add_after.space(1)
                self.updater.add_section(section)
                self.updater[section].update(expected_config)
                self.dirty = True
            parser[section] = expected_config
        return self.contents_without_top_section(self.get_example_cfg(parser))

    # TODO: refactor: convert the contents to dict (with IniConfig().sections?) and mimic other plugins doing dict diffs
    def enforce_rules(self) -> Iterator[Fuss]:
        """Enforce rules on missing sections and missing key/value pairs in an INI file."""
        try:
            yield from self._read_file()
        except Error:
            return

        yield from self.enforce_missing_sections()

        csv_sections = {v.split(SECTION_SEPARATOR)[0] for v in self.comma_separated_values}
        missing_csv = csv_sections.difference(self.current_sections)
        if missing_csv:
            yield self.reporter.make_fuss(
                Violations.INVALID_COMMA_SEPARATED_VALUES_SECTION, ", ".join(sorted(missing_csv))
            )
            # Don't continue if the comma-separated values are invalid
            return

        for section in self.expected_sections.intersection(self.current_sections) - self.missing_sections:
            yield from self.enforce_section(section)

    def _read_file(self) -> Iterator[Fuss]:
        """Read the .ini file or special files like .editorconfig."""
        parsing_err: Error | None = None
        try:
            self.updater.read(str(self.file_path))
        except MissingSectionHeaderError as err:
            if self.needs_top_section:
                original_contents = self.file_path.read_text()
                self.updater.read_string(f"[{TOP_SECTION}]\n{original_contents}")
                return

            # If this is not an .editorconfig file, report this as a regular parsing error
            parsing_err = err
        except DuplicateOptionError as err:
            parsing_err = err

        if not parsing_err:
            return

        # Don't change the file if there was a parsing error
        self.autofix = False
        yield self.reporter.make_fuss(Violations.PARSING_ERROR, cls=parsing_err.__class__.__name__, msg=parsing_err)
        raise Error

    def enforce_missing_sections(self) -> Iterator[Fuss]:
        """Enforce missing sections."""
        missing = self.get_missing_output()
        if missing:
            yield self.reporter.make_fuss(Violations.MISSING_SECTIONS, missing, self.autofix)

    def enforce_section(self, section: str) -> Iterator[Fuss]:
        """Enforce rules for a section."""
        expected_dict = self.expected_config[section]
        actual_dict = {k: v.value for k, v in self.updater[section].items()}
        # TODO: refactor: add a class Ini(BaseDoc) and move this dictdiffer code there
        for diff_type, key, values in dictdiffer.diff(actual_dict, expected_dict):
            if diff_type == dictdiffer.CHANGE:
                if f"{section}.{key}" in self.comma_separated_values:
                    yield from self.enforce_comma_separated_values(section, key, values[0], values[1])
                else:
                    yield from self.compare_different_keys(section, key, values[0], values[1])
            elif diff_type == dictdiffer.ADD:
                yield from self.show_missing_keys(section, values)

    def enforce_comma_separated_values(self, section, key, raw_actual: Any, raw_expected: Any) -> Iterator[Fuss]:
        """Enforce sections and keys with comma-separated values. The values might contain spaces."""
        actual_set = {s.strip() for s in raw_actual.split(",")}
        expected_set = {s.strip() for s in raw_expected.split(",")}
        missing = expected_set - actual_set
        if not missing:
            return

        joined_values = ",".join(sorted(missing))
        value_to_append = f",{joined_values}"
        if self.autofix:
            self.updater[section][key].value += value_to_append
            self.dirty = True
        section_header = "" if section == TOP_SECTION else f"[{section}]\n"
        # TODO: test: top section with separated values in https://github.com/andreoliwa/nitpick/issues/271
        yield self.reporter.make_fuss(
            Violations.MISSING_VALUES_IN_LIST,
            f"{section_header}{key} = (...){value_to_append}",
            key=key,
            fixed=self.autofix,
        )

    def compare_different_keys(self, section, key, raw_actual: Any, raw_expected: Any) -> Iterator[Fuss]:
        """Compare different keys, with special treatment when they are lists or numeric."""
        if isinstance(raw_actual, (int, float, bool)) or isinstance(raw_expected, (int, float, bool)):
            # A boolean "True" or "true" has the same effect on ConfigParser files.
            actual = str(raw_actual).lower()
            expected = str(raw_expected).lower()
        else:
            actual = raw_actual
            expected = raw_expected
        if actual == expected:
            return

        if self.autofix:
            self.updater[section][key].value = expected
            self.dirty = True
        if section == TOP_SECTION:
            yield self.reporter.make_fuss(
                Violations.TOP_SECTION_HAS_DIFFERENT_VALUE,
                f"{key} = {raw_expected}",
                key=key,
                actual=raw_actual,
                fixed=self.autofix,
            )
        else:
            yield self.reporter.make_fuss(
                Violations.OPTION_HAS_DIFFERENT_VALUE,
                f"[{section}]\n{key} = {raw_expected}",
                section=section,
                key=key,
                actual=raw_actual,
                fixed=self.autofix,
            )

    def show_missing_keys(self, section: str, values: list[tuple[str, Any]]) -> Iterator[Fuss]:
        """Show the keys that are not present in a section."""
        parser = ConfigParser()
        missing_dict = dict(values)
        parser[section] = missing_dict
        output = self.get_example_cfg(parser)
        self.add_options_before_space(section, missing_dict)

        if section == TOP_SECTION:
            yield self.reporter.make_fuss(
                Violations.TOP_SECTION_MISSING_OPTION, self.contents_without_top_section(output), self.autofix
            )
        else:
            yield self.reporter.make_fuss(Violations.MISSING_OPTION, output, self.autofix, section=section)

    def add_options_before_space(self, section: str, options: dict) -> None:
        """Add new options before a blank line in the end of the section."""
        if not self.autofix:
            return

        space_removed = False
        while isinstance(self.updater[section].last_block, Space):
            space_removed = True
            self.updater[section].last_block.detach()

        self.updater[section].update(options)
        self.dirty = True

        if space_removed:
            self.updater[section].last_block.add_after.space(1)

    @staticmethod
    def get_example_cfg(parser: ConfigParser) -> str:
        """Print an example of a config parser in a string instead of a file."""
        string_stream = StringIO()
        parser.write(string_stream)
        output = string_stream.getvalue().strip()
        return output


@hookimpl
def plugin_class() -> type[NitpickPlugin]:
    """Handle INI files."""
    return IniPlugin


@hookimpl
def can_handle(info: FileInfo) -> type[NitpickPlugin] | None:
    """Handle INI files."""
    if IniPlugin.identify_tags & info.tags:
        return IniPlugin
    return None
