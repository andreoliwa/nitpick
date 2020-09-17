.. include:: targets.rst

.. _defaults:

Defaults
========

If you don't :ref:`configure your own style <configure-your-own-style>`, those are some of the defaults that will be applied.

All TOML_ configs below are taken from the `default style file`_.

.. auto-generated-from-here

.. _default-absent-files:

Absent files
------------

Content of `styles/absent-files.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/absent-files.toml>`_:

.. code-block:: toml

    [nitpick.files.absent]
    "requirements.txt" = "Install poetry, run 'poetry init' to create pyproject.toml, and move dependencies to it"
    ".isort.cfg" = "Move values to setup.cfg, section [isort]"
    "Pipfile" = "Use pyproject.toml instead"
    "Pipfile.lock" = "Use pyproject.toml instead"
    ".venv" = ""
    ".pyup.yml" = "Configure .travis.yml with safety instead: https://github.com/pyupio/safety#using-safety-with-a-ci-service"

.. _default-black:

black_
------

Content of `styles/black.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/black.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/python/black
        rev: 20.8b1
        hooks:
          - id: black
            args: [--safe, --quiet]
      - repo: https://github.com/asottile/blacken-docs
        rev: v1.8.0
        hooks:
          - id: blacken-docs
            additional_dependencies: [black==20.8b1]
    """
    # TODO The toml library has issues loading arrays with multiline strings:
    #  https://github.com/uiri/toml/issues/123
    #  https://github.com/uiri/toml/issues/230
    #  If they are fixed one day, remove this 'yaml' key and use only a 'repos' list with a single element:
    #["pre-commit-config.yaml"]
    #repos = ["""
    #<YAML goes here>
    #"""]

.. _default-flake8:

flake8_
-------

Content of `styles/flake8.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/flake8.toml>`_:

.. code-block:: toml

    ["setup.cfg".flake8]
    # http://www.pydocstyle.org/en/2.1.1/error_codes.html
    # Ignoring W503: https://github.com/python/black#line-breaks--binary-operators
    # Ignoring "D202 No blank lines allowed after function docstring": black inserts a blank line.
    ignore = "D107,D202,D203,D401,E203,E402,E501,W503"
    max-line-length = 120
    inline-quotes = "double"
    exclude = ".tox,build"

    # Nitpick recommends those plugins as part of the style, but doesn't install them automatically as before.
    # This way, the developer has the choice of overriding this style, instead of having lots of plugins installed
    # without being asked.
    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://gitlab.com/pycqa/flake8
        rev: 3.8.3
        hooks:
          - id: flake8
            additional_dependencies: [flake8-blind-except, flake8-bugbear, flake8-comprehensions,
              flake8-debugger, flake8-docstrings, flake8-isort, flake8-polyfill,
              flake8-pytest, flake8-quotes, yesqa]
    """
    # TODO suggest nitpick for external repos

.. _default-ipython:

IPython_
--------

Content of `styles/ipython.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/ipython.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    ipython = "*"
    ipdb = "*"

.. _default-isort:

isort_
------

Content of `styles/isort.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/isort.toml>`_:

.. code-block:: toml

    ["setup.cfg".isort]
    line_length = 120
    skip = ".tox,build"
    known_first_party = "tests"

    # The configuration below is needed for compatibility with black.
    # https://github.com/python/black#how-black-wraps-lines
    # https://github.com/timothycrosley/isort#multi-line-output-modes
    multi_line_output = 3
    include_trailing_comma = true
    force_grid_wrap = 0
    combine_as_imports = true

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/asottile/seed-isort-config
        rev: v2.2.0
        hooks:
          - id: seed-isort-config
      - repo: https://github.com/pre-commit/mirrors-isort
        rev: v5.5.2
        hooks:
          - id: isort
    """

.. _default-mypy:

mypy_
-----

Content of `styles/mypy.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/mypy.toml>`_:

.. code-block:: toml

    # https://mypy.readthedocs.io/en/latest/config_file.html
    ["setup.cfg".mypy]
    ignore_missing_imports = true

    # Do not follow imports (except for ones found in typeshed)
    follow_imports = "skip"

    # Treat Optional per PEP 484
    strict_optional = true

    # Ensure all execution paths are returning
    warn_no_return = true

    # Lint-style cleanliness for typing
    warn_redundant_casts = true
    warn_unused_ignores = true

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/mirrors-mypy
        rev: v0.782
        hooks:
          - id: mypy
    """

.. _default-package-json:

package.json_
-------------

Content of `styles/package-json.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/package-json.toml>`_:

.. code-block:: toml

    ["package.json"]
    contains_keys = ["name", "version", "repository.type", "repository.url", "release.plugins"]

    ["package.json".contains_json]
    commitlint = """
      {
        "extends": [
          "@commitlint/config-conventional"
        ]
      }
    """

.. _default-poetry:

Poetry_
-------

Content of `styles/poetry.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/poetry.toml>`_:

.. code-block:: toml

    [nitpick.files.present]
    "pyproject.toml" = "Install poetry and run 'poetry init' to create it"

.. _default-bash:

Bash_
-----

Content of `styles/pre-commit/bash.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pre-commit/bash.toml>`_:

.. code-block:: toml

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/openstack/bashate
        rev: 2.0.0
        hooks:
          - id: bashate
    """

.. _default-commitlint:

commitlint_
-----------

Content of `styles/pre-commit/commitlint.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pre-commit/commitlint.toml>`_:

.. code-block:: toml

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
        rev: v3.0.0
        hooks:
          - id: commitlint
            stages: [commit-msg]
            additional_dependencies: ['@commitlint/config-conventional']
    """

.. _default-pre-commit-hooks:

pre-commit_ (hooks)
-------------------

Content of `styles/pre-commit/general.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pre-commit/general.toml>`_:

.. code-block:: toml

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v3.2.0
        hooks:
          - id: debug-statements
          - id: end-of-file-fixer
          - id: trailing-whitespace
      - repo: https://github.com/asottile/pyupgrade
        rev: v2.7.2
        hooks:
          - id: pyupgrade
    """

.. _default-pre-commit-main:

pre-commit_ (main)
------------------

Content of `styles/pre-commit/main.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pre-commit/main.toml>`_:

.. code-block:: toml

    # See https://pre-commit.com for more information
    # See https://pre-commit.com/hooks.html for more hooks

    [nitpick.files.present]
    ".pre-commit-config.yaml" = "Create the file with the contents below, then run 'pre-commit install'"

.. _default-pre-commit-python-hooks:

pre-commit_ (Python hooks)
--------------------------

Content of `styles/pre-commit/python.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pre-commit/python.toml>`_:

.. code-block:: toml

    [["pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pygrep-hooks
        rev: v1.6.0
        hooks:
          - id: python-check-blanket-noqa
          - id: python-check-mock-methods
          - id: python-no-eval
          - id: python-no-log-warn
          - id: rst-backticks
    """

.. _default-pylint:

Pylint_
-------

Content of `styles/pylint.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/pylint.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    pylint = "*"

.. _default-python-3-5-3-6-3-7-to-3-8:

Python 3.5, 3.6, 3.7 to 3.8
---------------------------

Content of `styles/python35-36-37-38.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/python35-36-37-38.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.5 || ^3.6 || ^3.7 || ^3.8"

.. _default-python-3-5-3-6-or-3-7:

Python 3.5, 3.6 or 3.7
----------------------

Content of `styles/python35-36-37.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/python35-36-37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.5 || ^3.6 || ^3.7"

.. _default-python-3-6-or-3-7:

Python 3.6 or 3.7
-----------------

Content of `styles/python36-37.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/python36-37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.6 || ^3.7"

.. _default-python-3-6:

Python 3.6
----------

Content of `styles/python36.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/python36.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.6"

.. _default-python-3-7:

Python 3.7
----------

Content of `styles/python37.toml <https://raw.githubusercontent.com/andreoliwa/nitpick/develop/styles/python37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.7"
