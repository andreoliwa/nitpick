Nitpick
=======

|PyPI|
|Supported Python versions|
|GitHub Actions Python Workflow|
|Documentation Status|
|Coveralls|
|Maintainability|
|Test Coverage|
|pre-commit|
|pre-commit.ci status|
|Project License|
|Code style: black|
|Renovate|
|semantic-release|
|FOSSA Status|

Command-line tool and `flake8 <https://github.com/PyCQA/flake8>`_
plugin to enforce the same settings across multiple language-independent
projects.

Useful if you maintain multiple projects and are tired of
copying/pasting the same INI/TOML/YAML/JSON keys and values over and
over, in all of them.

The CLI now has a ``nitpick fix`` command that modifies configuration
files directly (pretty much like
`black <https://github.com/psf/black>`_ and
`isort <https://github.com/PyCQA/isort>`_ do with Python files).
See the `CLI docs for more
info <https://nitpick.rtfd.io/en/latest/cli.html>`_.

Many more features are planned for the future, check `the
roadmap <https://github.com/andreoliwa/nitpick/projects/1>`_.

The style file
--------------

A "Nitpick code style" is a `TOML <https://github.com/toml-lang/toml>`_
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

-  ... `black <https://github.com/psf/black>`_,
   `isort <https://github.com/PyCQA/isort>`_ and
   `flake8 <https://github.com/PyCQA/flake8>`_ have a line length of
   120;
-  ... `flake8 <https://github.com/PyCQA/flake8>`_ and
   `isort <https://github.com/PyCQA/isort>`_ are configured as above in
   ``setup.cfg``;
-  ... `Pylint <https://www.pylint.org>`__ is present as a
   `Poetry <https://github.com/python-poetry/poetry>`_ dev dependency
   in ``pyproject.toml``.

Supported file types
--------------------

These are the file types currently handled by Nitpick.

-  Some files are only being checked and have to be modified manually;
-  Some files can already be fixed automatically (with the
   ``nitpick fix`` command);
-  Others are still under construction; the ticket numbers are shown in
   the table (upvote the ticket with 👍🏻 if you would like to prioritise
   development).

Implemented
~~~~~~~~~~~

.. auto-generated-start-implemented
.. list-table::
   :header-rows: 1

   * - File type
     - ``nitpick check``
     - ``nitpick fix``
   * - `Any INI file <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_
     - ✅
     - ✅
   * - `Any JSON file <https://nitpick.rtfd.io/en/latest/plugins.html#json-files>`_
     - ✅
     - ✅
   * - `Any plain text file <https://nitpick.rtfd.io/en/latest/plugins.html#text-files>`_
     - ✅
     - ❌
   * - `Any TOML file <https://nitpick.rtfd.io/en/latest/plugins.html#toml-files>`_
     - ✅
     - ✅
   * - `Any YAML file <https://nitpick.rtfd.io/en/latest/plugins.html#yaml-files>`_
     - ✅
     - ✅
   * - `.editorconfig <https://nitpick.rtfd.io/en/latest/library.html#any>`_
     - ✅
     - ✅
   * - `.pylintrc <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_
     - ✅
     - ✅
   * - `setup.cfg <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_
     - ✅
     - ✅
.. auto-generated-end-implemented

Planned
~~~~~~~

.. auto-generated-start-planned
.. list-table::
   :header-rows: 1

   * - File type
     - ``nitpick check``
     - ``nitpick fix``
   * - Any Markdown file
     - `#280 <https://github.com/andreoliwa/nitpick/issues/280>`_ 🚧
     - ❓
   * - Any Terraform file
     - `#318 <https://github.com/andreoliwa/nitpick/issues/318>`_ 🚧
     - ❓
   * - Dockerfile
     - `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧
     - `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧
   * - .dockerignore
     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧
     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧
   * - .gitignore
     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧
     - `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧
   * - Jenkinsfile
     - `#278 <https://github.com/andreoliwa/nitpick/issues/278>`_ 🚧
     - ❓
   * - Makefile
     - `#277 <https://github.com/andreoliwa/nitpick/issues/277>`_ 🚧
     - ❓
.. auto-generated-end-planned

Style Library (Presets)
-----------------------

Nitpick has a builtin library of style presets, shipped as `Python resources <https://docs.python.org/3/library/importlib.html#module-importlib.resources>`_.

This library contains building blocks for your your custom style.
Just choose styles from the table below and create your own style, like LEGO.

Read how to:

- `...add multiple styles to the configuration file <https://nitpick.readthedocs.io/en/latest/configuration.html#multiple-styles>`_;
- `...include styles inside a style <https://nitpick.readthedocs.io/en/latest/nitpick_section.html#nitpick-styles>`_.

.. auto-generated-start-style-library

any
~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/any/codeclimate <src/nitpick/resources/any/codeclimate.toml>`_
     - `CodeClimate <https://codeclimate.com/>`_
   * - `py://nitpick/resources/any/commitizen <src/nitpick/resources/any/commitizen.toml>`_
     - `Commitizen (Python) <https://github.com/commitizen-tools/commitizen>`_
   * - `py://nitpick/resources/any/commitlint <src/nitpick/resources/any/commitlint.toml>`_
     - `commitlint <https://github.com/conventional-changelog/commitlint>`_
   * - `py://nitpick/resources/any/editorconfig <src/nitpick/resources/any/editorconfig.toml>`_
     - `EditorConfig <http://editorconfig.org/>`_
   * - `py://nitpick/resources/any/git-legal <src/nitpick/resources/any/git-legal.toml>`_
     - `Git.legal - CodeClimate Community Edition <https://github.com/kmewhort/git.legal-codeclimate>`_
   * - `py://nitpick/resources/any/markdownlint <src/nitpick/resources/any/markdownlint.toml>`_
     - `Markdown lint <https://github.com/markdownlint/markdownlint>`_
   * - `py://nitpick/resources/any/pre-commit-hooks <src/nitpick/resources/any/pre-commit-hooks.toml>`_
     - `pre-commit hooks for any project <https://github.com/pre-commit/pre-commit-hooks>`_
   * - `py://nitpick/resources/any/prettier <src/nitpick/resources/any/prettier.toml>`_
     - `Prettier <https://github.com/prettier/prettier>`_

javascript
~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/javascript/package-json <src/nitpick/resources/javascript/package-json.toml>`_
     - `package.json <https://github.com/yarnpkg/website/blob/master/lang/en/docs/package-json.md>`_

kotlin
~~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/kotlin/ktlint <src/nitpick/resources/kotlin/ktlint.toml>`_
     - `ktlint <https://github.com/pinterest/ktlint>`_

presets
~~~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/presets/nitpick <src/nitpick/resources/presets/nitpick.toml>`_
     - `Default style file for Nitpick <https://nitpick.rtfd.io/>`_

proto
~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/proto/protolint <src/nitpick/resources/proto/protolint.toml>`_
     - `protolint (Protobuf linter) <https://github.com/yoheimuta/protolint>`_

python
~~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/python/310 <src/nitpick/resources/python/310.toml>`_
     - Python 3.10
   * - `py://nitpick/resources/python/37 <src/nitpick/resources/python/37.toml>`_
     - Python 3.7
   * - `py://nitpick/resources/python/38 <src/nitpick/resources/python/38.toml>`_
     - Python 3.8
   * - `py://nitpick/resources/python/39 <src/nitpick/resources/python/39.toml>`_
     - Python 3.9
   * - `py://nitpick/resources/python/absent <src/nitpick/resources/python/absent.toml>`_
     - Files that should not exist
   * - `py://nitpick/resources/python/autoflake <src/nitpick/resources/python/autoflake.toml>`_
     - `autoflake <https://github.com/myint/autoflake>`_
   * - `py://nitpick/resources/python/bandit <src/nitpick/resources/python/bandit.toml>`_
     - `Bandit <https://github.com/PyCQA/bandit>`_
   * - `py://nitpick/resources/python/black <src/nitpick/resources/python/black.toml>`_
     - `Black <https://github.com/psf/black>`_
   * - `py://nitpick/resources/python/flake8 <src/nitpick/resources/python/flake8.toml>`_
     - `Flake8 <https://github.com/PyCQA/flake8>`_
   * - `py://nitpick/resources/python/github-workflow <src/nitpick/resources/python/github-workflow.toml>`_
     - `GitHub Workflow for Python <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>`_
   * - `py://nitpick/resources/python/ipython <src/nitpick/resources/python/ipython.toml>`_
     - `IPython <https://github.com/ipython/ipython>`_
   * - `py://nitpick/resources/python/isort <src/nitpick/resources/python/isort.toml>`_
     - `isort <https://github.com/PyCQA/isort>`_
   * - `py://nitpick/resources/python/mypy <src/nitpick/resources/python/mypy.toml>`_
     - `Mypy <https://github.com/python/mypy>`_
   * - `py://nitpick/resources/python/poetry-editable <src/nitpick/resources/python/poetry-editable.toml>`_
     - `Poetry (editable projects; PEP 600 support) <https://github.com/python-poetry/poetry>`_
   * - `py://nitpick/resources/python/poetry <src/nitpick/resources/python/poetry.toml>`_
     - `Poetry <https://github.com/python-poetry/poetry>`_
   * - `py://nitpick/resources/python/pre-commit-hooks <src/nitpick/resources/python/pre-commit-hooks.toml>`_
     - `pre-commit hooks for Python projects <https://pre-commit.com/hooks>`_
   * - `py://nitpick/resources/python/pylint <src/nitpick/resources/python/pylint.toml>`_
     - `Pylint <https://github.com/PyCQA/pylint>`_
   * - `py://nitpick/resources/python/radon <src/nitpick/resources/python/radon.toml>`_
     - `Radon <https://github.com/rubik/radon>`_
   * - `py://nitpick/resources/python/readthedocs <src/nitpick/resources/python/readthedocs.toml>`_
     - `Read the Docs <https://github.com/readthedocs/readthedocs.org>`_
   * - `py://nitpick/resources/python/sonar-python <src/nitpick/resources/python/sonar-python.toml>`_
     - `SonarQube Python plugin <https://github.com/SonarSource/sonar-python>`_
   * - `py://nitpick/resources/python/stable <src/nitpick/resources/python/stable.toml>`_
     - Current stable Python version
   * - `py://nitpick/resources/python/tox <src/nitpick/resources/python/tox.toml>`_
     - `tox <https://github.com/tox-dev/tox>`_

shell
~~~~~

.. list-table::
   :header-rows: 1

   * - Style URL
     - Description
   * - `py://nitpick/resources/shell/bashate <src/nitpick/resources/shell/bashate.toml>`_
     - `bashate (code style for Bash) <https://github.com/openstack/bashate>`_
   * - `py://nitpick/resources/shell/shellcheck <src/nitpick/resources/shell/shellcheck.toml>`_
     - `ShellCheck (static analysis for shell scripts) <https://github.com/koalaman/shellcheck>`_
   * - `py://nitpick/resources/shell/shfmt <src/nitpick/resources/shell/shfmt.toml>`_
     - `shfmt (shell script formatter) <https://github.com/mvdan/sh>`_
.. auto-generated-end-style-library

Quickstart
----------

Install
~~~~~~~

Install in an isolated global environment with
`pipx <https://github.com/pipxproject/pipx>`_::

    # Latest PyPI release
    pipx install nitpick

    # Development branch from GitHub
    pipx install git+https://github.com/andreoliwa/nitpick

On macOS/Linux, install with
`Homebrew <https://github.com/Homebrew/brew>`_::

    # Latest PyPI release
    brew install andreoliwa/formulae/nitpick

    # Development branch from GitHub
    brew install andreoliwa/formulae/nitpick --HEAD

On Arch Linux, install with yay::

    yay -Syu nitpick

Add to your project with
`Poetry <https://github.com/python-poetry/poetry>`_::

    poetry add --dev nitpick

Or install it with pip::

    pip install -U nitpick

Run
~~~

To fix and modify your files directly::

    nitpick fix

To check for errors only::

    nitpick check

Nitpick is also a ``flake8`` plugin, so you can run this on a project
with at least one Python (``.py``) file::

    flake8 .

Nitpick will download and use the opinionated `default style file <nitpick-style.toml>`_.

You can use it as a template to configure your own style.

Run as a pre-commit hook
~~~~~~~~~~~~~~~~~~~~~~~~

If you use `pre-commit <https://pre-commit.com/>`_ on your project, add
this to the ``.pre-commit-config.yaml`` in your repository::

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.32.0
        hooks:
          - id: nitpick

There are 3 available hook IDs:

- ``nitpick`` and ``nitpick-fix`` both run the ``nitpick fix`` command;
- ``nitpick-check`` runs ``nitpick check``.

If you want to run Nitpick as a flake8 plugin instead::

    repos:
      - repo: https://github.com/PyCQA/flake8
        rev: 4.0.1
        hooks:
          - id: flake8
            additional_dependencies: [nitpick]

More information
----------------

Nitpick is being used by projects such as:

-  `wemake-services/wemake-python-styleguide <https://github.com/wemake-services/wemake-python-styleguide>`_
-  `dry-python/returns <https://github.com/dry-python/returns>`_
-  `sobolevn/django-split-settings <https://github.com/sobolevn/django-split-settings>`_
-  `catalyst-team/catalyst <https://github.com/catalyst-team/catalyst>`_
-  `alan-turing-institute/AutSPACEs <https://github.com/alan-turing-institute/AutSPACEs>`_
-  `pytest-dev/pytest-mimesis <https://github.com/pytest-dev/pytest-mimesis>`_

For more details on styles and which configuration files are currently
supported, `see the full documentation <https://nitpick.rtfd.io/>`_.

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
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |pre-commit.ci status| image:: https://results.pre-commit.ci/badge/github/andreoliwa/nitpick/develop.svg
   :target: https://results.pre-commit.ci/latest/github/andreoliwa/nitpick/develop
.. |FOSSA Status| image:: https://app.fossa.com/api/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick.svg?type=shield
   :target: https://app.fossa.com/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick?ref=badge_shield

Contributing
------------

Your help is very much appreciated.

There are many possibilities for new features in this project, and not enough time or hands to work on them.

If you want to contribute with the project, set up your development environment following the steps on the `contribution guidelines <https://nitpick.rtfd.io/en/latest/contributing.html>`_ and send your pull request.
