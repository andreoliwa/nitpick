Nitpick
=======

.. _default style file: https://raw.githubusercontent.com/andreoliwa/nitpick/v0.20.0/nitpick-style.toml
.. _TOML: https://github.com/toml-lang/toml
.. _flake8: https://gitlab.com/pycqa/flake8
.. _isort: https://github.com/timothycrosley/isort
.. _black: https://github.com/psf/black
.. _mypy: http://mypy-lang.org/
.. _pylint: https://www.pylint.org
.. _pre-commit: https://pre-commit.com/
.. _poetry: https://github.com/sdispater/poetry/

.. image:: https://img.shields.io/pypi/v/nitpick.svg
    :target: https://pypi.python.org/pypi/nitpick
    :alt: PyPI
.. image:: https://travis-ci.com/andreoliwa/nitpick.svg
    :target: https://travis-ci.com/andreoliwa/nitpick
    :alt: Travis CI
.. image:: https://readthedocs.org/projects/nitpick/badge/?version=latest
    :target: https://nitpick.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg
    :target: https://coveralls.io/github/andreoliwa/nitpick
    :alt: Coveralls
.. image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability
    :target: https://codeclimate.com/github/andreoliwa/nitpick/maintainability
    :alt: Maintainability
.. image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage
    :target: https://codeclimate.com/github/andreoliwa/nitpick/test_coverage
    :alt: Test Coverage
.. image:: https://img.shields.io/pypi/pyversions/nitpick.svg
    :target: https://pypi.org/project/nitpick/
    :alt: Supported Python versions
.. image:: https://img.shields.io/pypi/l/nitpick.svg
    :target: https://pypi.org/project/nitpick/
    :alt: Project License
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code style: black
.. image:: https://api.dependabot.com/badges/status?host=github&repo=andreoliwa/nitpick
    :target: https://dependabot.com
    :alt: Dependabot Status
.. image:: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg
    :target: https://github.com/semantic-release/semantic-release
    :alt: semantic-release

Flake8 plugin to enforce the same tool configuration (flake8_, isort_, mypy_, pylint_...) across multiple Python projects.

Useful if you maintain multiple projects and want to use the same configs in all of them.

.. warning::

    This project is still experimental and the API is not fully defined:

    - The style file syntax might slightly change before the 1.0 stable release.
    - The numbers in the ``NIP*`` error codes might change.

Style file
----------

A "nitpick code style" is a TOML_ file with the settings that should be present in config files from other tools.

Example of a style:

.. code-block::

    ["pyproject.toml".tool.black]
    line-length = 120

    ["pyproject.toml".tool.poetry.dev-dependencies]
    pylint = "*"

    ["setup.cfg".flake8]
    ignore = "D107,D202,D203,D401"
    max-line-length = 120
    inline-quotes = "double"

    ["setup.cfg".isort]
    line_length = 120
    multi_line_output = 3
    include_trailing_comma = true
    force_grid_wrap = 0
    combine_as_imports = true

This style will assert that:

- ... black_, isort_ and flake8_ have a line length of 120;
- ... flake8_ and isort_ are configured as above in ``setup.cfg``;
- ... pylint_ is present as a project dev dependency (in ``pyproject.toml``, used by poetry_).

Quick setup
-----------

To try the package, simply install it (in a virtualenv or globally, wherever) and run ``flake8``:

.. code-block::

    $ pip install -U nitpick
    $ flake8

``nitpick`` will use the opinionated `default style file`_.

You can use it as a template to create your own style.

Run as a pre-commit hook (recommended)
--------------------------------------

If you use pre-commit_ on your project (you should), add this to the ``.pre-commit-config.yaml`` in your repository:

.. code-block::

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.20.0
        hooks:
          - id: nitpick

.. toctree::
   :caption: Contents:

   self
   styles
   config
   supported_files
   contributing
   authors

.. toctree::
   :maxdepth: 1
   :caption: API:

   source/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

To Do List
==========

.. todolist::
