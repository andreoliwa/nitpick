# -*- coding: utf-8 -*-
"""
Setup for this package.

.. note::

    This file was generated automatically by ``poetryx setup-py``.
    A ``setup.py`` file is needed to install this project in editable mode (``pip install -e /path/to/project``).

    `See this and other utilities from the clib package <https://github.com/andreoliwa/python-clib#poetryx>`_.
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
    "version": "0.21.0",
    "description": "Flake8 plugin to enforce the same lint configuration (flake8, isort, mypy, pylint) across multiple Python projects",
    "long_description": '# Nitpick\n\n[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.org/project/nitpick)\n[![Travis CI](https://api.travis-ci.com/andreoliwa/nitpick.svg)](https://travis-ci.com/andreoliwa/nitpick)\n[![Documentation Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.rtfd.io/en/latest/?badge=latest)\n[![Coveralls](https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg)](https://coveralls.io/github/andreoliwa/nitpick)\n[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick)\n[![Test Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick)\n[![Supported Python versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)\n[![Project License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)\n[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)\n[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=andreoliwa/nitpick)](https://dependabot.com)\n[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)\n\nFlake8 plugin to enforce the same tool configuration ([flake8](https://gitlab.com/pycqa/flake8), [isort](https://github.com/timothycrosley/isort), [mypy](http://mypy-lang.org/), [Pylint](https://www.pylint.org)...) across multiple Python projects.\n\nUseful if you maintain multiple projects and want to use the same configs in all of them.\n\n## Style file\n\nA "nitpick code style" is a [TOML](https://github.com/toml-lang/toml) file with the settings that should be present in config files from other tools.\n\nExample of a style:\n\n```\n["pyproject.toml".tool.black]\nline-length = 120\n\n["pyproject.toml".tool.poetry.dev-dependencies]\npylint = "*"\n\n["setup.cfg".flake8]\nignore = "D107,D202,D203,D401"\nmax-line-length = 120\ninline-quotes = "double"\n\n["setup.cfg".isort]\nline_length = 120\nmulti_line_output = 3\ninclude_trailing_comma = true\nforce_grid_wrap = 0\ncombine_as_imports = true\n```\n\nThis style will assert that:\n\n- ... [black](https://github.com/psf/black), [isort](https://github.com/timothycrosley/isort) and [flake8](https://gitlab.com/pycqa/flake8) have a line length of 120;\n- ... [flake8](https://gitlab.com/pycqa/flake8) and [isort](https://github.com/timothycrosley/isort) are configured as above in `setup.cfg`;\n- ... [Pylint](https://www.pylint.org) is present as a [Poetry](https://github.com/sdispater/poetry/) dev dependency in `pyproject.toml`).\n\n## Quick setup\n\nTo try the package, simply install it (in a virtualenv or globally, wherever) and run `flake8`:\n\n    $ pip install -U nitpick\n    $ flake8\n\nNitpick will download and use the opinionated [default style file](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.21.0/nitpick-style.toml).\n\nYou can use it as a template to configure your own style.\n\n### Run as a pre-commit hook (recommended)\n\nIf you use [pre-commit](https://pre-commit.com/) on your project (you should), add this to the `.pre-commit-config.yaml` in your repository:\n\n    repos:\n      - repo: https://github.com/andreoliwa/nitpick\n        rev: v0.21.0\n        hooks:\n          - id: nitpick\n\n---\n\nFor more details on styles and which configuration files are currently supported, [see the full documentation](https://nitpick.rtfd.io/).\n',
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
