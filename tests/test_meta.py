"""Meta tests."""
from pipfile import Pipfile

# Copied from setup.py
# TODO: Open the .py file and parse/eval
REQUIRED = [
    "flake8",
    "flake8-blind-except",
    "flake8-bugbear",
    "flake8-comprehensions",
    "flake8-debugger",
    "flake8-docstrings",
    "flake8-isort",
    "flake8-mypy",
    "flake8-polyfill",
    "flake8-pytest",
    "flake8-quotes",
    "ipython",
    "ipdb",
]


def test_setup_matches_pipfile():
    """Check if the contents of the Pipfile match what's declared on setup.py."""
    pip_file = Pipfile.load("Pipfile")
    pip_file_packages = [
        "{}{}".format(package, "" if version == "*" else version)
        for package, version in pip_file.data["default"].items()
    ]
    assert sorted(REQUIRED) == sorted(pip_file_packages)
