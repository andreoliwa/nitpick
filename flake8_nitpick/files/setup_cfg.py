"""Checker for the setup.cfg config file."""
import itertools
from configparser import ConfigParser
from io import StringIO
from typing import Any, List, Set, Tuple

import dictdiffer

from flake8_nitpick.files.base import BaseFile
from flake8_nitpick.types import YieldFlake8Error


class SetupCfgFile(BaseFile):
    """Check setup.cfg."""

    file_name = "setup.cfg"
    error_base_number = 320

    COMMA_SEPARATED_VALUES = "comma_separated_values"
    comma_separated_values: Set[str]

    def check_rules(self) -> YieldFlake8Error:
        """Check missing sections and missing key/value pairs in setup.cfg."""
        if not self.file_path.exists():
            return

        self.comma_separated_values = set(self.file_toml.pop(self.COMMA_SEPARATED_VALUES, []))

        setup_cfg = ConfigParser()
        setup_cfg.read_file(self.file_path.open())

        actual_sections = set(setup_cfg.sections())
        expected_sections = set(self.file_toml.keys())
        missing_sections = expected_sections - actual_sections

        if missing_sections:
            missing_cfg = ConfigParser()
            for section in missing_sections:
                missing_cfg[section] = self.file_toml[section]
            output = self.get_example_cfg(missing_cfg)
            yield self.flake8_error(1, f"Missing sections:\n{output}")

        generators = []
        for section in expected_sections - missing_sections:
            expected_dict = self.file_toml[section]
            actual_dict = dict(setup_cfg[section])
            for diff_type, key, values in dictdiffer.diff(expected_dict, actual_dict):
                if diff_type == dictdiffer.CHANGE:
                    generators.append(self.compare_different_keys(section, key, values[0], values[1]))
                elif diff_type == dictdiffer.REMOVE:
                    generators.append(self.show_missing_keys(section, key, values))
        for error in itertools.chain(*generators):
            yield error

    def compare_different_keys(self, section, key, raw_expected: Any, raw_actual: Any) -> YieldFlake8Error:
        """Compare different keys, with special treatment when they are lists or numeric."""
        combined = f"{section}.{key}"
        if combined in self.comma_separated_values:
            # The values might contain spaces
            actual_set = {s.strip() for s in raw_actual.split(",")}
            expected_set = {s.strip() for s in raw_expected.split(",")}
            missing = expected_set - actual_set
            if missing:
                yield self.flake8_error(2, f"Missing values in key\n[{section}]\n{key} = {','.join(sorted(missing))}")
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
                3, f"Expected value {raw_expected!r} in key, got {raw_actual!r}\n[{section}]\n{key} = {raw_expected}"
            )

    def show_missing_keys(self, section, key, values: List[Tuple[str, Any]]) -> YieldFlake8Error:
        """Show the keys that are not present in a section."""
        missing_cfg = ConfigParser()
        missing_cfg[section] = dict(values)
        output = self.get_example_cfg(missing_cfg)
        yield self.flake8_error(4, f"Missing keys in section:\n{output}")

    @staticmethod
    def get_example_cfg(config_parser: ConfigParser) -> str:
        """Print an example of a config parser in a string instead of a file."""
        string_stream = StringIO()
        config_parser.write(string_stream)
        output = string_stream.getvalue().strip()
        return output
