# -*- coding: utf-8 -*-
"""NOTICE: This file was generated automatically by the command: xpoetry setup-py."""
from distutils.core import setup

packages = ["flake8_nitpick"]

package_data = {"": ["*"]}

install_requires = ["attrs", "dictdiffer", "flake8>=3.0.0", "pyyaml", "requests", "toml"]

entry_points = {"flake8.extension": ["NIP = flake8_nitpick:NitpickChecker"]}

setup_kwargs = {
    "name": "flake8-nitpick",
    "version": "0.7.1",
    "description": "Flake8 plugin to share the same code style for multiple Python projects",
    "long_description": '==============\nflake8-nitpick\n==============\n\n.. image:: https://img.shields.io/pypi/v/flake8-nitpick.svg\n        :target: https://pypi.python.org/pypi/flake8-nitpick\n\n.. image:: https://travis-ci.com/andreoliwa/flake8-nitpick.svg?branch=master\n    :target: https://travis-ci.com/andreoliwa/flake8-nitpick\n\n.. image:: https://coveralls.io/repos/github/andreoliwa/flake8-nitpick/badge.svg?branch=master\n    :target: https://coveralls.io/github/andreoliwa/flake8-nitpick?branch=master\n\n.. image:: https://pyup.io/repos/github/andreoliwa/flake8-nitpick/shield.svg\n     :target: https://pyup.io/repos/github/andreoliwa/flake8-nitpick/\n     :alt: Updates\n\nFlake8 plugin to share the same code style for multiple Python projects.\n\nA "nitpick code style" is a `TOML <https://github.com/toml-lang/toml>`_ file with settings that should be present in config files from other tools. E.g.:\n\n- ``pyproject.toml`` and ``setup.cfg`` (used by `flake8 <http://flake8.pycqa.org/>`_, `black <https://black.readthedocs.io/>`_, `isort <https://isort.readthedocs.io/>`_, `mypy <https://mypy.readthedocs.io/>`_);\n- ``.pylintrc`` (used by `pylint <https://pylint.readthedocs.io/>`_ config);\n- more files to come.\n\nQuick setup\n-----------\n\nSimply install the package (in a virtualenv or globally, wherever) and run ``flake8``:\n\n.. code-block:: console\n\n    $ pip install -U flake8-nitpick\n    $ flake8\n\nYou will see warnings if your project configuration is different than `the default style file <https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml>`_.\n\nConfigure your own style file\n-----------------------------\n\nChange your project config on ``pyproject.toml``, and configure your own style like this:\n\n.. code-block:: ini\n\n    [tool.nitpick]\n    style = "https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml"\n\nYou can set ``style`` with any local file or URL. E.g.: you can use the raw URL of a `GitHub Gist <https://gist.github.com>`_.\n\nDefault search order for a style file\n-------------------------------------\n\n1. A file or URL configured in the ``pyproject.toml`` file, ``[tool.nitpick]`` section, ``style`` key, as `described above <Configure your own style file>`_.\n\n2. Any ``nitpick-style.toml`` file found in the current directory (the one in which ``flake8`` runs from) or above.\n\n3. If no style is found, then `the default style file from GitHub <https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/nitpick-style.toml>`_ is used.\n\nStyle file syntax\n-----------------\n\nA style file contains basically the configuration options you want to enforce in all your projects.\n\nThey are just the config to the tool, prefixed with the name of the config file.\n\nE.g.: To `configure the black formatter <https://github.com/ambv/black#configuration-format>`_ with a line length of 120, you use this in your ``pyproject.toml``:\n\n.. code-block:: ini\n\n    [tool.black]\n    line-length = 120\n\nTo enforce that all your projects use this same line length, add this to your ``nitpick-style.toml`` file:\n\n.. code-block:: ini\n\n    ["pyproject.toml".tool.black]\n    line-length = 120\n\nIt\'s the same exact section/key, just prefixed with the config file name (``"pyproject.toml".``)\n\nThe same works for ``setup.cfg``.\nTo `configure mypy <https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format>`_ to ignore missing imports in your project:\n\n.. code-block:: ini\n\n    [mypy]\n    ignore_missing_imports = true\n\nTo enforce all your projects to ignore missing imports, add this to your ``nitpick-style.toml`` file:\n\n.. code-block:: ini\n\n    ["setup.cfg".mypy]\n    ignore_missing_imports = true\n\nAbsent files\n------------\n\nTo enforce that certain files should not exist in the project, you can add them to the style file.\n\n.. code-block:: ini\n\n    [[files.absent]]\n    file = "myfile1.txt"\n\n    [[files.absent]]\n    file = "another_file.env"\n    message = "This is an optional extra string to display after the warning"\n\nMultiple files can be configured as above.\nThe ``message`` is optional.\n\nComma separated values (setup.cfg)\n----------------------------------\n\nOn ``setup.cfg``, some keys are lists of multiple values separated by commas, like ``flake8.ignore``.\n\nOn the style file, it\'s possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.\nMultiple keys can be added.\n\n.. code-block:: ini\n\n    ["setup.cfg"]\n    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]\n',
    "author": "Augusto Wagner Andreoli",
    "author_email": "andreoliwa@gmail.com",
    "url": "https://github.com/andreoliwa/flake8-nitpick",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "python_requires": ">=3.6,<4.0",
}


setup(**setup_kwargs)  # type: ignore
