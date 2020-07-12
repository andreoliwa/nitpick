"""Checker for the `setup.cfg <https://docs.python.org/3/distutils/configfile.html>` config file."""
from configparser import ConfigParser
from io import StringIO
from typing import Any, Dict, List, Optional, Set, Tuple, Type

import dictdiffer

from nitpick.plugins import hookimpl
from nitpick.plugins.base import NitpickPlugin
from nitpick.typedefs import JsonDict, YieldFlake8Error


class SetupCfgPlugin(NitpickPlugin):
    """Checker for the `setup.cfg <https://docs.python.org/3/distutils/configfile.html>`_ config file.

    Example: :ref:`flake8 configuration <default-flake8>`.
    """

    file_name = "setup.cfg"
    error_base_number = 320
    COMMA_SEPARATED_VALUES = "comma_separated_values"

    expected_sections = set()  # type: Set[str]
    missing_sections = set()  # type: Set[str]

    def __init__(self, config: JsonDict, file_name: str = None) -> None:
        super().__init__(config, file_name)
        self.comma_separated_values = set(self.nitpick_file_dict.get(self.COMMA_SEPARATED_VALUES, []))  # type: Set[str]

    def suggest_initial_contents(self) -> str:
        """Suggest the initial content for this missing file."""
        return self.get_missing_output()

    def get_missing_output(self, actual_sections: Set[str] = None) -> str:
        """Get a missing output string example from the missing sections in setup.cfg."""
        self.expected_sections = set(self.file_dict.keys())
        self.missing_sections = self.expected_sections - (actual_sections or set())

        if self.missing_sections:
            missing_cfg = ConfigParser()
            for section in sorted(self.missing_sections):
                expected_config = self.file_dict[section]  # type: Dict
                if not isinstance(expected_config, dict):
                    # Silently ignore invalid sections for now, to avoid exceptions.
                    # This should be solved in https://github.com/andreoliwa/nitpick/issues/69
                    continue
                missing_cfg[section] = expected_config
            return self.get_example_cfg(missing_cfg)
        return ""

    def check_rules(self) -> YieldFlake8Error:
        """Check missing sections and missing key/value pairs in setup.cfg."""
        setup_cfg = ConfigParser()
        with self.file_path.open() as handle:
            setup_cfg.read_file(handle)

        actual_sections = set(setup_cfg.sections())
        missing = self.get_missing_output(actual_sections)
        if missing:
            yield self.flake8_error(1, " has some missing sections. Use this:", missing)

        for section in self.expected_sections - self.missing_sections:
            expected_dict = self.file_dict[section]
            actual_dict = dict(setup_cfg[section])
            # TODO: add a class Ini(BaseFormat) and move this dictdiffer code there
            for diff_type, key, values in dictdiffer.diff(actual_dict, expected_dict):
                if diff_type == dictdiffer.CHANGE:
                    yield from self.compare_different_keys(section, key, values[0], values[1])
                elif diff_type == dictdiffer.ADD:
                    yield from self.show_missing_keys(section, key, values)

    def compare_different_keys(self, section, key, raw_actual: Any, raw_expected: Any) -> YieldFlake8Error:
        """Compare different keys, with special treatment when they are lists or numeric."""
        combined = "{}.{}".format(section, key)
        if combined in self.comma_separated_values:
            # The values might contain spaces
            actual_set = {s.strip() for s in raw_actual.split(",")}
            expected_set = {s.strip() for s in raw_expected.split(",")}
            missing = expected_set - actual_set
            if missing:
                yield self.flake8_error(
                    2,
                    " has missing values in the {!r} key. Include those values:".format(key),
                    "[{}]\n{} = (...),{}".format(section, key, ",".join(sorted(missing))),
                )
            return

        if isinstance(raw_actual, (int, float, bool)) or isinstance(raw_expected, (int, float, bool)):
            # A boolean "True" or "true" has the same effect on setup.cfg.
            actual = str(raw_actual).lower()
            expected = str(raw_expected).lower()
        else:
            actual = raw_actual
            expected = raw_expected
        if actual != expected:
            yield self.flake8_error(
                3,
                ": [{}]{} is {} but it should be like this:".format(section, key, raw_actual),
                "[{}]\n{} = {}".format(section, key, raw_expected),
            )

    def show_missing_keys(  # pylint: disable=unused-argument
        self, section, key, values: List[Tuple[str, Any]]
    ) -> YieldFlake8Error:
        """Show the keys that are not present in a section."""
        missing_cfg = ConfigParser()
        missing_cfg[section] = dict(values)
        output = self.get_example_cfg(missing_cfg)
        yield self.flake8_error(4, ": section [{}] has some missing key/value pairs. Use this:".format(section), output)

    @staticmethod
    def get_example_cfg(config_parser: ConfigParser) -> str:
        """Print an example of a config parser in a string instead of a file."""
        string_stream = StringIO()
        config_parser.write(string_stream)
        output = string_stream.getvalue().strip()
        return output


@hookimpl
def plugin_class() -> Type["NitpickPlugin"]:
    """You should return your plugin class here."""
    return SetupCfgPlugin


@hookimpl
def handle_config_file(  # pylint: disable=unused-argument
    config: JsonDict, file_name: str, tags: Set[str]
) -> Optional["NitpickPlugin"]:
    """Handle the setup.cfg file."""
    return SetupCfgPlugin(config) if file_name == SetupCfgPlugin.file_name else None
