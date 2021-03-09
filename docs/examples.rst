.. include:: targets.rst

.. _examples:

Examples
========

If you don't :ref:`configure your own style <configure-your-own-style>`, those are some of the defaults that will be applied.

All TOML_ configs below are taken from the `default style file`_.

You can use these examples directly with their URL (see :ref:`multiple_styles`), or copy/paste the TOML into your own style file.

.. auto-generated-from-here

.. _example-absent-files:

Absent files
------------

Contents of `styles/absent-files.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/absent-files.toml>`_:

.. code-block:: toml

    [nitpick.files.absent]
    "requirements.txt" = "Install poetry, run 'poetry init' to create pyproject.toml, and move dependencies to it"
    ".isort.cfg" = "Move values to setup.cfg, section [isort]"
    "Pipfile" = "Use pyproject.toml instead"
    "Pipfile.lock" = "Use pyproject.toml instead"
    ".venv" = ""
    ".pyup.yml" = "Configure safety instead: https://github.com/pyupio/safety#using-safety-with-a-ci-service"

.. _example-black:

black_
------

Contents of `styles/black.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/black.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/psf/black
        rev: 20.8b1
        hooks:
          - id: black
            args: [--safe, --quiet]
      - repo: https://github.com/asottile/blacken-docs
        rev: v1.9.2
        hooks:
          - id: blacken-docs
            additional_dependencies: [black==20.8b1]
    """
    # TODO The toml library has issues loading arrays with multiline strings:
    #  https://github.com/uiri/toml/issues/123
    #  https://github.com/uiri/toml/issues/230
    #  If they are fixed one day, remove this 'yaml' key and use only a 'repos' list with a single element:
    #[".pre-commit-config.yaml"]
    #repos = ["""
    #<YAML goes here>
    #"""]

.. _example-editorconfig:

EditorConfig_
-------------

Contents of `styles/editorconfig.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/editorconfig.toml>`_:

.. code-block:: toml

    # http://editorconfig.org/

    [".editorconfig"]
    # top-most EditorConfig file
    root = true

    [".editorconfig"."*"]
    # Unix-style newlines with a newline ending every file
    end_of_line = "lf"
    insert_final_newline = true
    indent_style = "space"
    indent_size = 4

    # Whitespace at the end of lines
    trim_trailing_whitespace = true

    # Matches multiple files with brace expansion notation
    # Set default charset
    [".editorconfig"."*.{js,json}"]
    charset = "utf-8"
    indent_size = 2

    [".editorconfig"."*.py"]
    charset = "utf-8"

    [".editorconfig"."*.{yml,yaml,md}"]
    indent_size = 2

    [".editorconfig".Makefile]
    indent_style = "tab"

.. _example-flake8:

flake8_
-------

Contents of `styles/flake8.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/flake8.toml>`_:

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
    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://gitlab.com/pycqa/flake8
        rev: 3.8.4
        hooks:
          - id: flake8
            additional_dependencies:
              [
                flake8-blind-except,
                flake8-bugbear,
                flake8-comprehensions,
                flake8-debugger,
                flake8-docstrings,
                flake8-isort,
                flake8-polyfill,
                flake8-pytest,
                flake8-quotes,
                flake8-typing-imports,
                yesqa,
              ]
    """
    # TODO suggest nitpick for external repos

.. _example-ipython:

IPython_
--------

Contents of `styles/ipython.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/ipython.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    ipython = "*"
    ipdb = "*"

.. _example-isort:

isort_
------

Contents of `styles/isort.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/isort.toml>`_:

.. code-block:: toml

    ["setup.cfg".isort]
    line_length = 120
    skip = ".tox,build"
    known_first_party = "tests"

    # The configuration below is needed for compatibility with black.
    # https://github.com/python/black#how-black-wraps-lines
    # https://github.com/PyCQA/isort#multi-line-output-modes
    multi_line_output = 3
    include_trailing_comma = true
    force_grid_wrap = 0
    combine_as_imports = true

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/PyCQA/isort
        rev: 5.7.0
        hooks:
          - id: isort
    """

.. _example-mypy:

mypy_
-----

Contents of `styles/mypy.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/mypy.toml>`_:

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

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/mirrors-mypy
        rev: v0.812
        hooks:
          - id: mypy
    """

.. _example-package-json:

package.json_
-------------

Contents of `styles/package-json.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/package-json.toml>`_:

.. code-block::

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

.. _example-poetry:

Poetry_
-------

Contents of `styles/poetry.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/poetry.toml>`_:

.. code-block:: toml

    [nitpick.files.present]
    "pyproject.toml" = "Install poetry and run 'poetry init' to create it"

.. _example-bash:

Bash_
-----

Contents of `styles/pre-commit/bash.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pre-commit/bash.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/openstack/bashate
        rev: 2.0.0
        hooks:
          - id: bashate
    """

.. _example-commitlint:

commitlint_
-----------

Contents of `styles/pre-commit/commitlint.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pre-commit/commitlint.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
        rev: v4.1.0
        hooks:
          - id: commitlint
            stages: [commit-msg]
            additional_dependencies: ['@commitlint/config-conventional']
    """

.. _example-pre-commit-hooks:

pre-commit_ (hooks)
-------------------

Contents of `styles/pre-commit/general.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pre-commit/general.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v3.4.0
        hooks:
          - id: debug-statements
          - id: end-of-file-fixer
          - id: trailing-whitespace
      - repo: https://github.com/asottile/pyupgrade
        rev: v2.10.0
        hooks:
          - id: pyupgrade
    """

.. _example-pre-commit-main:

pre-commit_ (main)
------------------

Contents of `styles/pre-commit/main.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pre-commit/main.toml>`_:

.. code-block:: toml

    # See https://pre-commit.com for more information
    # See https://pre-commit.com/hooks.html for more hooks

    [nitpick.files.present]
    ".pre-commit-config.yaml" = "Create the file with the contents below, then run 'pre-commit install'"

.. _example-pre-commit-python-hooks:

pre-commit_ (Python hooks)
--------------------------

Contents of `styles/pre-commit/python.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pre-commit/python.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pygrep-hooks
        rev: v1.8.0
        hooks:
          - id: python-check-blanket-noqa
          - id: python-check-mock-methods
          - id: python-no-eval
          - id: python-no-log-warn
          - id: rst-backticks
    """

.. _example-pylint:

Pylint_
-------

Contents of `styles/pylint.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/pylint.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    pylint = "*"

.. _example-python-3-6:

Python 3.6
----------

Contents of `styles/python36.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/python36.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.6"

.. _example-python-3-7:

Python 3.7
----------

Contents of `styles/python37.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/python37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.7"

.. _example-python-3-8:

Python 3.8
----------

Contents of `styles/python38.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/python38.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.8"

.. _example-python-3-9:

Python 3.9
----------

Contents of `styles/python39.toml <https://github.com/andreoliwa/nitpick/blob/v0.24.1/styles/python39.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.9"
