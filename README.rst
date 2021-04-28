Nitpick
=======

| |PyPI|
| |GitHub Actions Python Workflow|
| |Documentation Status|
| |Coveralls|
| |Maintainability|
| |Test Coverage|
| |Supported Python versions|
| |Project License|
| |Code style: black|
| |Renovate|
| |semantic-release|
| |pre-commit.ci status|

Command-line tool and `flake8 <https://github.com/PyCQA/flake8>`__
plugin to enforce the same settings across multiple language-independent
projects.

Useful if you maintain multiple projects and are tired of
copying/pasting the same INI/TOML/YAML/JSON keys and values over and
over, in all of them.

The CLI now has a ``nitpick fix`` command that modifies configuration
files directly (pretty much like
`black <https://github.com/psf/black>`__ and
`isort <https://github.com/PyCQA/isort>`__ do with Python files).
See the `CLI docs for more
info <https://nitpick.rtfd.io/en/latest/cli.html>`__.

Many more features are planned for the future, check `the
roadmap <https://github.com/andreoliwa/nitpick/projects/1>`__.

Style file
----------

A "nitpick code style" is a `TOML <https://github.com/toml-lang/toml>`__
file with the settings that should be present in config files from other
tools.

Example of a style:

.. code-block:: toml

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

-  ... `black <https://github.com/psf/black>`__,
   `isort <https://github.com/PyCQA/isort>`__ and
   `flake8 <https://github.com/PyCQA/flake8>`__ have a line length of
   120;
-  ... `flake8 <https://github.com/PyCQA/flake8>`__ and
   `isort <https://github.com/PyCQA/isort>`__ are configured as above in
   ``setup.cfg``;
-  ... `Pylint <https://www.pylint.org>`__ is present as a
   `Poetry <https://github.com/python-poetry/poetry>`__ dev dependency
   in ``pyproject.toml``).

Supported file types
--------------------

These are the file types currently handled by Nitpick.

-  Some files are only being checked and have to be modified manually;
-  Some files can already be fixed automatically (with the
   ```nitpick fix`` <#run>`__ command);
-  Others are still under construction; the ticket numbers are shown in
   the table (upvote the ticket with 👍🏻 if you would like to prioritise
   development).

Implemented
~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - File type
     - ``nitpick check``
     - ``nitpick fix``
   * - `Any .ini file <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_
     - ✅
     - ✅
   * - `Any .json file <https://nitpick.rtfd.io/en/latest/plugins.html#json-files>`_
     - ✅
     - 🚧 `#358 <https://github.com/andreoliwa/nitpick/issues/358>`_

+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| `Any .toml file <https://nitpick.rtfd.io/en/latest/plugins.html#toml-files>`__                        | ✅                              | ✅                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| `Any text file <https://nitpick.rtfd.io/en/latest/plugins.html#text-files>`__                             | ✅                              | ❌                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```.editorconfig`` <https://nitpick.rtfd.io/en/latest/examples.html#example-editorconfig>`__              | ✅                              | ✅                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```.pre-commit-config.yaml`` <https://nitpick.rtfd.io/en/latest/plugins.html#pre-commit-config-yaml>`__   | ✅                              | 🚧  \ `#282 <https://github.com/andreoliwa/nitpick/issues/282>`__   |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```.pylintrc`` <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`__                              | ✅                              | ✅                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```package.json`` <https://nitpick.rtfd.io/en/latest/examples.html#example-package-json>`__               | ✅                              | 🚧  \ `#358 <https://github.com/andreoliwa/nitpick/issues/358>`__   |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```pyproject.toml`` <https://nitpick.rtfd.io/en/latest/plugins.html#toml-files>`__                        | ✅                              | ✅                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```requirements.txt`` <https://nitpick.rtfd.io/en/latest/plugins.html#text-files>`__                      | ✅                              | ❌                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+
| ```setup.cfg`` <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`__                              | ✅                              | ✅                                                                  |
+-----------------------------------------------------------------------------------------------------------+--------------------------------+--------------------------------------------------------------------+

.. raw:: html

   <!-- auto-generated-end-implemented -->

Planned
~~~~~~~

+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
|                       |                                        | ` <#run>`__                                         |
+================================+====================================================================+====================================================================+
| Any ``.md`` (Markdown) file    | 🚧  \ `#280 <https://github.com/andreoliwa/nitpick/issues/280>`__   | ❓                                                                  |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| Any ``.tf`` (Terraform) file   | 🚧  \ `#318 <https://github.com/andreoliwa/nitpick/issues/318>`__   | ❓                                                                  |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``.dockerignore``              | 🚧  \ `#8 <https://github.com/andreoliwa/nitpick/issues/8>`__       | 🚧  \ `#8 <https://github.com/andreoliwa/nitpick/issues/8>`__       |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``.gitignore``                 | 🚧  \ `#8 <https://github.com/andreoliwa/nitpick/issues/8>`__       | 🚧  \ `#8 <https://github.com/andreoliwa/nitpick/issues/8>`__       |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``.travis.yml``                | 🚧  \ `#15 <https://github.com/andreoliwa/nitpick/issues/15>`__     | 🚧  \ `#15 <https://github.com/andreoliwa/nitpick/issues/15>`__     |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``Dockerfile``                 | 🚧  \ `#272 <https://github.com/andreoliwa/nitpick/issues/272>`__   | 🚧  \ `#272 <https://github.com/andreoliwa/nitpick/issues/272>`__   |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``Jenkinsfile``                | 🚧  \ `#278 <https://github.com/andreoliwa/nitpick/issues/278>`__   | ❓                                                                  |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+
| ``Makefile``                   | 🚧  \ `#277 <https://github.com/andreoliwa/nitpick/issues/277>`__   | ❓                                                                  |
+--------------------------------+--------------------------------------------------------------------+--------------------------------------------------------------------+

.. raw:: html

   <!-- auto-generated-end-planned -->

Quickstart
----------

Install
~~~~~~~

Install in an isolated environment with
`pipx <https://github.com/pipxproject/pipx>`__:

::

    # Latest PyPI release
    pipx install nitpick

    # Development branch from GitHub
    pipx install git+https://github.com/andreoliwa/nitpick

On macOS/Linux, install the latest release with
`Homebrew <https://github.com/Homebrew/brew>`__:

::

    brew install andreoliwa/formulae/nitpick

    # Development branch from GitHub
    brew install andreoliwa/formulae/nitpick --HEAD

On Arch Linux, install with yay:

::

    yay -Syu nitpick

Add to your project with
`Poetry <https://github.com/python-poetry/poetry>`__:

::

    poetry add --dev nitpick

Or install it with pip:

::

    pip install -U nitpick

Run
~~~

To fix and modify your files directly:

::

    nitpick fix

To check for errors only:

::

    nitpick check

Nitpick is also a ``flake8`` plugin, so you can run this on a project
with at least one Python (``.py``) file:

::

    flake8 .

Nitpick will download and use the opinionated `default style
file <https://raw.githubusercontent.com/andreoliwa/nitpick/v0.26.0/nitpick-style.toml>`__.

You can use it as a template to configure your own style.

Run as a pre-commit hook
~~~~~~~~~~~~~~~~~~~~~~~~

If you use `pre-commit <https://pre-commit.com/>`__ on your project, add
this to the ``.pre-commit-config.yaml`` in your repository:

::

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.26.0
        hooks:
          - id: nitpick

To install the ``pre-commit`` and ``commit-msg`` Git hooks:

::

    pre-commit install --install-hooks
    pre-commit install -t commit-msg

To start checking all your code against the default rules:

::

    pre-commit run --all-files

More information
----------------

Nitpick is being used by projects such as:

-  `wemake-services/wemake-python-styleguide <https://github.com/wemake-services/wemake-python-styleguide>`__
-  `dry-python/returns <https://github.com/dry-python/returns>`__
-  `sobolevn/django-split-settings <https://github.com/sobolevn/django-split-settings>`__
-  `catalyst-team/catalyst <https://github.com/catalyst-team/catalyst>`__
-  `alan-turing-institute/AutSPACEs <https://github.com/alan-turing-institute/AutSPACEs>`__
-  `pytest-dev/pytest-mimesis <https://github.com/pytest-dev/pytest-mimesis>`__

For more details on styles and which configuration files are currently
supported, `see the full documentation <https://nitpick.rtfd.io/>`__.

.. |PyPI| image:: https://img.shields.io/pypi/v/nitpick.svg
   :target: https://pypi.org/project/nitpick
.. |GitHub Actions Python Workflow| image:: https://github.com/andreoliwa/nitpick/workflows/Python/badge.svg
.. |Documentation Status| image:: https://readthedocs.org/projects/nitpick/badge/?version=latest
   :target: https://nitpick.rtfd.io/en/latest/?badge=latest
.. |Coveralls| image:: https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg
   :target: https://coveralls.io/github/andreoliwa/nitpick
.. |Maintainability| image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability
   :target: https://codeclimate.com/github/andreoliwa/nitpick
.. |Test Coverage| image:: https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage
   :target: https://codeclimate.com/github/andreoliwa/nitpick
.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/nitpick.svg
   :target: https://pypi.org/project/nitpick/
.. |Project License| image:: https://img.shields.io/pypi/l/nitpick.svg
   :target: https://pypi.org/project/nitpick/
.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Renovate| image:: https://img.shields.io/badge/renovate-enabled-brightgreen.svg
   :target: https://renovatebot.com/
.. |semantic-release| image:: https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg
   :target: https://github.com/semantic-release/semantic-release
.. |pre-commit.ci status| image:: https://results.pre-commit.ci/badge/github/andreoliwa/nitpick/develop.svg
   :target: https://results.pre-commit.ci/latest/github/andreoliwa/nitpick/develop
