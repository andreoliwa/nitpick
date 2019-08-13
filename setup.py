# -*- coding: utf-8 -*-
"""
Setup for this package.

.. note::

    This file was generated automatically by ``xpoetry setup-py``.
    A ``setup.py`` file is needed to install this project in editable mode (``pip install -e /path/to/project``).
"""
# pylint: disable=line-too-long
from distutils.core import setup

package_dir = {"": "src"}

packages = ["nitpick", "nitpick.files"]

package_data = {"": ["*"]}

install_requires = [
    "attrs",
    "click",
    "dictdiffer",
    "flake8>=3.0.0",
    "jmespath",
    "marshmallow-polyfield>=5.7,<6.0",
    "marshmallow>=3.0.0b10",
    "python-slugify",
    "requests",
    "ruamel.yaml",
    "sortedcontainers",
    "toml",
]

entry_points = {"flake8.extension": ["NIP = nitpick.plugin:NitpickChecker"]}

setup_kwargs = {
    "name": "nitpick",
    "version": "0.20.0",
    "description": "Flake8 plugin to enforce the same lint configuration (flake8, isort, mypy, pylint) across multiple Python projects",
    "long_description": '# nitpick\n\n[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.python.org/pypi/nitpick)\n[![Travis CI](https://travis-ci.com/andreoliwa/nitpick.svg)](https://travis-ci.com/andreoliwa/nitpick)\n[![Documentation Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.readthedocs.io/en/latest/?badge=latest)\n[![Coveralls](https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg)](https://coveralls.io/github/andreoliwa/nitpick)\n[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick/maintainability)\n[![Test Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick/test_coverage)\n[![Supported Python versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)\n[![Project License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)\n[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=andreoliwa/nitpick)](https://dependabot.com)\n[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)\n\nFlake8 plugin to enforce the same lint configuration (flake8, isort, mypy, pylint) across multiple Python projects.\n\nA "nitpick code style" is a [TOML](https://github.com/toml-lang/toml) file with settings that should be present in config files from other tools. E.g.:\n\n- `pyproject.toml` and `setup.cfg` (used by [flake8](http://flake8.pycqa.org/), [black](https://black.readthedocs.io/), [isort](https://isort.readthedocs.io/), [mypy](https://mypy.readthedocs.io/));\n- `.pylintrc` (used by [pylint](https://pylint.readthedocs.io/) config);\n- more files to come.\n\n---\n\n- [Installation and usage](#installation-and-usage)\n- [Style file](#style-file)\n- [setup.cfg](#setupcfg)\n\n---\n\n## Installation and usage\n\nTo try the package, simply install it (in a virtualenv or globally, wherever) and run `flake8`:\n\n    $ pip install -U nitpick\n    $ flake8\n\nYou will see warnings if your project configuration is different than [the default style file](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.20.0/nitpick-style.toml).\n\n### As a pre-commit hook\n\nIf you use [pre-commit](https://pre-commit.com/) on your project, add this to the `.pre-commit-config.yaml` in your repository:\n\n    repos:\n      - repo: https://github.com/andreoliwa/nitpick\n        rev: v0.20.0\n        hooks:\n          # Run nitpick and several other flake8 plugins\n          - id: nitpick-all\n          # Check only nitpick errors, ignore other flake8 plugins\n          - id: nitpick-only\n\nUse one hook or the other (`nitpick-all` **or** `nitpick-only`), not both.\nTo check all the other flake8 plugins that are installed with `nitpick`, see the [pyproject.toml](pyproject.toml).\n\n## Style file\n\n### Configure your own style file\n\nChange your project config on `pyproject.toml`, and configure your own style like this:\n\n    [tool.nitpick]\n    style = "https://raw.githubusercontent.com/andreoliwa/nitpick/v0.20.0/nitpick-style.toml"\n\nYou can set `style` with any local file or URL. E.g.: you can use the raw URL of a [GitHub Gist](https://gist.github.com).\n\nYou can also use multiple styles and mix local files and URLs:\n\n    [tool.nitpick]\n    style = ["/path/to/first.toml", "/another/path/to/second.toml", "https://example.com/on/the/web/third.toml"]\n\nThe order is important: each style will override any keys that might be set by the previous .toml file.\nIf a key is defined in more than one file, the value from the last file will prevail.\n\n### Default search order for a style file\n\n1. A file or URL configured in the `pyproject.toml` file, `[tool.nitpick]` section, `style` key, as [described above](#configure-your-own-style-file).\n\n2. Any `nitpick-style.toml` file found in the current directory (the one in which `flake8` runs from) or above.\n\n3. If no style is found, then [the default style file from GitHub](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.20.0/nitpick-style.toml) is used.\n\n### Style file syntax\n\nNOTE: The project is still experimental; the style file syntax might slightly change before the 1.0 stable release.\n\nA style file contains basically the configuration options you want to enforce in all your projects.\n\nThey are just the config to the tool, prefixed with the name of the config file.\n\nE.g.: To [configure the black formatter](https://github.com/python/black#configuration-format) with a line length of 120, you use this in your `pyproject.toml`:\n\n    [tool.black]\n    line-length = 120\n\nTo enforce that all your projects use this same line length, add this to your `nitpick-style.toml` file:\n\n    ["pyproject.toml".tool.black]\n    line-length = 120\n\nIt\'s the same exact section/key, just prefixed with the config file name (`"pyproject.toml".`)\n\nThe same works for `setup.cfg`.\nTo [configure mypy](https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format) to ignore missing imports in your project:\n\n    [mypy]\n    ignore_missing_imports = true\n\nTo enforce all your projects to ignore missing imports, add this to your `nitpick-style.toml` file:\n\n    ["setup.cfg".mypy]\n    ignore_missing_imports = true\n\n### Absent files\n\nTo enforce that certain files should not exist in the project, you can add them to the style file.\n\n    [nitpick.files.absent]\n    "some_file.txt" = "This is an optional extra string to display after the warning"\n    "another_file.env" = ""\n\nMultiple files can be configured as above.\nThe message is optional.\n\n## setup.cfg\n\n### Comma separated values\n\nOn `setup.cfg`, some keys are lists of multiple values separated by commas, like `flake8.ignore`.\n\nOn the style file, it\'s possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.\nMultiple keys can be added.\n\n    [nitpick.files."setup.cfg"]\n    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]\n',
    "author": "W. Augusto Andreoli",
    "author_email": "andreoliwa@gmail.com",
    "url": "https://github.com/andreoliwa/nitpick",
    "package_dir": package_dir,
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.5,<4.0",
}


setup(**setup_kwargs)  # type: ignore
