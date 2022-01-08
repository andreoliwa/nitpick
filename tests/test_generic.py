"""Generic functions tests."""
import os
import sys
from pathlib import Path
from unittest import mock

from testfixtures import compare

from nitpick.constants import EDITOR_CONFIG, TOX_INI
from nitpick.generic import get_subclasses, relative_to_current_dir
from tests.helpers import assert_conditions


def test_get_subclasses():
    """Test subclasses."""

    # pylint: disable=missing-docstring,too-few-public-methods
    class Vehicle:
        pass

    class Car(Vehicle):
        pass

    class Audi(Car):
        pass

    class Bicycle(Vehicle):
        pass

    assert_conditions(get_subclasses(Vehicle) == [Car, Audi, Bicycle])


@mock.patch.object(Path, "cwd")
@mock.patch.object(Path, "home")
def test_relative_to_current_dir(home, cwd):
    """Mock the home and current dirs, and test relative paths to them (testing Linux-only)."""
    if sys.platform == "win32":
        home_dir = "C:\\Users\\john"
        project_dir = f"{home_dir}\\project"
    else:
        home_dir = "/home/john"
        project_dir = f"{home_dir}/project"
    home.return_value = Path(home_dir)
    cwd.return_value = Path(project_dir)
    sep = os.path.sep

    examples = {
        None: "",
        project_dir: "",
        Path(project_dir): "",
        f"{home_dir}{sep}another": f"{home_dir}{sep}another",
        Path(f"{home_dir}{sep}bla{sep}bla"): f"{home_dir}{sep}bla{sep}bla",
        f"{project_dir}{sep}{TOX_INI}": TOX_INI,
        f"{project_dir}{sep}{EDITOR_CONFIG}": EDITOR_CONFIG,
        Path(f"{project_dir}{sep}apps{sep}manage.py"): f"apps{sep}manage.py",
        f"{home_dir}{sep}another{sep}one{sep}bites.py": f"{home_dir}{sep}another{sep}one{sep}bites.py",
        Path(f"{home_dir}{sep}bla{sep}bla.txt"): f"{home_dir}{sep}bla{sep}bla.txt",
    }
    if sys.platform == "win32":
        examples.update(
            {
                "d:\\Program Files\\MyApp": "d:\\Program Files\\MyApp",
                Path("d:\\Program Files\\AnotherApp"): "d:\\Program Files\\AnotherApp",
                "C:\\System32\\win32.dll": "C:\\System32\\win32.dll",
                Path("E:\\network\\file.txt"): "E:\\network\\file.txt",
            }
        )
    else:
        examples.update(
            {
                "/usr/bin/some": "/usr/bin/some",
                Path("/usr/bin/awesome"): "/usr/bin/awesome",
                "/usr/bin/something/wicked/this-way-comes.cfg": "/usr/bin/something/wicked/this-way-comes.cfg",
                Path("/usr/bin/.awesome"): "/usr/bin/.awesome",
            }
        )

    for path, expected in examples.items():
        compare(actual=relative_to_current_dir(path), expected=expected, prefix=f"Path: {path}")
