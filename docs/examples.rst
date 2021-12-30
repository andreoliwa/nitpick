.. include:: targets.rst

.. _examples:

Examples
========

If you don't :ref:`configure your own style <configure-your-own-style>`, those are some of the defaults that will be applied.

All TOML_ configs below are taken from the `default style file`_.

You can use these examples directly with their URL (see :ref:`multiple_styles`), or copy/paste the TOML into your own style file.

.. auto-generated-from-here

.. _example-commitizen:

commitizen_
-----------

Contents of `resources/any/commitizen.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/any/commitizen.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/commitizen-tools/commitizen
        hooks:
          - id: commitizen
            stages: [commit-msg]
    """

.. _example-commitlint:

commitlint_
-----------

Contents of `resources/any/commitlint.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/any/commitlint.toml>`_:

.. code-block::

    ["package.json".contains_json]
    commitlint = """
      {
        "extends": [
          "@commitlint/config-conventional"
        ]
      }
    """

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
        hooks:
          - id: commitlint
            stages: [commit-msg]
            additional_dependencies: ['@commitlint/config-conventional']
    """

.. _example-editorconfig:

EditorConfig_
-------------

Contents of `resources/any/editorconfig.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/any/editorconfig.toml>`_:

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

    [".editorconfig"."*.{yml,yaml,md,rb}"]
    indent_size = 2

    [".editorconfig".Makefile]
    indent_style = "tab"

.. _example-pre-commit-hooks:

pre-commit_ (hooks)
-------------------

Contents of `resources/any/hooks.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/any/hooks.toml>`_:

.. code-block:: toml

    # See https://pre-commit.com for more information
    # See https://pre-commit.com/hooks.html for more hooks

    [nitpick.files.present]
    ".pre-commit-config.yaml" = "Create the file with the contents below, then run 'pre-commit install'"

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pre-commit-hooks
        hooks:
          - id: end-of-file-fixer
          - id: trailing-whitespace
    """

.. _example-package-json:

package.json_
-------------

Contents of `resources/javascript/package-json.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/javascript/package-json.toml>`_:

.. code-block:: toml

    ["package.json"]
    contains_keys = ["name", "version", "repository.type", "repository.url", "release.plugins"]

.. _example-absent-files:

Absent files
------------

Contents of `resources/python/absent.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/absent.toml>`_:

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

Contents of `resources/python/black.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/black.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/psf/black
        hooks:
          - id: black
            args: [--safe, --quiet]
      - repo: https://github.com/asottile/blacken-docs
        hooks:
          - id: blacken-docs
            additional_dependencies: [black==21.5b2]
    """
    # TODO The toml library has issues loading arrays with multiline strings:
    #  https://github.com/uiri/toml/issues/123
    #  https://github.com/uiri/toml/issues/230
    #  If they are fixed one day, remove this 'yaml' key and use only a 'repos' list with a single element:
    #[".pre-commit-config.yaml"]
    #repos = ["""
    #<YAML goes here>
    #"""]

.. _example-flake8:

flake8_
-------

Contents of `resources/python/flake8.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/flake8.toml>`_:

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
      - repo: https://github.com/PyCQA/flake8
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

.. _example-pre-commit-python-hooks:

pre-commit_ (Python hooks)
--------------------------

Contents of `resources/python/hooks.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/hooks.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/pre-commit/pygrep-hooks
        hooks:
          - id: python-check-blanket-noqa
          - id: python-check-mock-methods
          - id: python-no-eval
          - id: python-no-log-warn
          - id: rst-backticks
      - repo: https://github.com/pre-commit/pre-commit-hooks
        hooks:
          - id: debug-statements
      - repo: https://github.com/asottile/pyupgrade
        hooks:
          - id: pyupgrade
    """

.. _example-ipython:

IPython_
--------

Contents of `resources/python/ipython.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/ipython.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    ipython = "*"
    ipdb = "*"

.. _example-isort:

isort_
------

Contents of `resources/python/isort.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/isort.toml>`_:

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
        hooks:
          - id: isort
    """

.. _example-mypy:

mypy_
-----

Contents of `resources/python/mypy.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/mypy.toml>`_:

.. code-block:: toml

    # https://mypy.readthedocs.io/en/latest/config_file.html
    ["setup.cfg".mypy]
    ignore_missing_imports = true

    # https://mypy.readthedocs.io/en/stable/running_mypy.html#follow-imports
    follow_imports = "normal"

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
        hooks:
          - id: mypy
    """

.. _example-poetry:

Poetry_
-------

Contents of `resources/python/poetry.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/poetry.toml>`_:

.. code-block:: toml

    [nitpick.files.present]
    "pyproject.toml" = "Install poetry and run 'poetry init' to create it"

.. _example-pylint:

Pylint_
-------

Contents of `resources/python/pylint.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/pylint.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    pylint = {version = "*", optional = true}

    ["pyproject.toml".tool.poetry.extras]
    lint = ["pylint"]

    [".pylintrc".MASTER]
    # Use multiple processes to speed up Pylint.
    jobs = 1

    [".pylintrc".REPORTS]
    # Set the output format. Available formats are text, parseable, colorized, msvs (visual studio) and html.
    # You can also give a reporter class, eg mypackage.mymodule.MyReporterClass.
    output-format = "colorized"

    [".pylintrc"."MESSAGES CONTROL"]
    # TODO: deal with character separated INI options in https://github.com/andreoliwa/nitpick/issues/271
    #  The "nitpick.files" section doesn't work out of the box for .pylintrc:
    #  [nitpick.files.".pylintrc"]
    #  comma_separated_values = ["MESSAGES CONTROL.disable"]
    #  This syntax will be deprecated anyway, so I won't make it work now
    # Configurations for the black formatter
    #disable = "bad-continuation,bad-whitespace,fixme,cyclic-import"

    [".pylintrc".BASIC]
    # List of builtins function names that should not be used, separated by a comma
    bad-functions = "map,filter"
    # Good variable names which should always be accepted, separated by a comma
    good-names = "i,j,k,e,ex,Run,_,id,rv"

    [".pylintrc".FORMAT]
    # Maximum number of characters on a single line.
    max-line-length = 120
    # Maximum number of lines in a module
    max-module-lines = 1000
    # TODO: deal with empty options (strings with spaces and quotes); maybe it's a ConfigParser/ConfigUpdater thing
    # String used as indentation unit. This is usually " " (4 spaces) or "\t" (1 tab).
    #indent-string = "    "
    # Number of spaces of indent required inside a hanging or continued line.
    indent-after-paren = 4

    [".pylintrc".SIMILARITIES]
    # Minimum lines number of a similarity.
    min-similarity-lines = 4
    # Ignore comments when computing similarities.
    ignore-comments = "yes"
    # Ignore docstrings when computing similarities.
    ignore-docstrings = "yes"
    # Ignore imports when computing similarities.
    ignore-imports = "no"

    [".pylintrc".VARIABLES]
    # A regular expression matching the name of dummy variables (i.e. expectedly not used).
    dummy-variables-rgx = "_$|dummy"

.. _example-python-3-10:

Python 3.10
-----------

Contents of `resources/python/python310.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/python310.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.10"

.. _example-python-3-6:

Python 3.6
----------

Contents of `resources/python/python36.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/python36.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.6.1"

.. _example-python-3-7:

Python 3.7
----------

Contents of `resources/python/python37.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/python37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.7"

.. _example-python-3-8:

Python 3.8
----------

Contents of `resources/python/python38.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/python38.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.8"

.. _example-python-3-9:

Python 3.9
----------

Contents of `resources/python/python39.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/python39.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.9"

.. _example-tox:

tox_
----

Contents of `resources/python/tox.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/python/tox.toml>`_:

.. code-block:: toml

    ["tox.ini".tox]
    # https://tox.readthedocs.io/en/latest/config.html
    isolated_build = true

    ["tox.ini".testenv]
    description = "Run tests with pytest and coverage"
    extras = "test"

    ["tox.ini"."coverage:run"]
    # https://coverage.readthedocs.io/en/latest/config.html#run
    branch = true
    parallel = true
    source = "src/"
    # TODO: deal with multiline INI values in https://github.com/andreoliwa/nitpick/issues/271
    #omit = """tests/*
    #.tox/*
    #*/pypoetry/virtualenvs/*
    #"""
    # This config is needed by https://github.com/marketplace/actions/coveralls-python#usage
    relative_files = true

    ["tox.ini"."coverage:report"]
    # https://coverage.readthedocs.io/en/latest/config.html#report
    show_missing = true
    precision = 2
    skip_covered = true
    skip_empty = true
    sort = "Cover"

.. _example-bash:

Bash_
-----

Contents of `resources/shell/hooks.toml <https://github.com/andreoliwa/nitpick/blob/v0.29.0/resources/shell/hooks.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    yaml = """
      - repo: https://github.com/openstack/bashate
        hooks:
          - id: bashate
    """
