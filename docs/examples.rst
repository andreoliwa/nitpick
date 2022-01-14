.. include:: targets.rst

.. _examples:

Examples
========

If you don't :ref:`configure your own style <configure-your-own-style>`, those are some of the defaults that will be applied.

All TOML_ configs below are taken from the `default style file`_.

You can use these examples directly with their URL (see :ref:`multiple_styles`), or copy/paste the TOML into your own style file.

.. auto-generated-from-here

.. _example-codeclimate:

codeclimate_
------------

Contents of `resources/any/codeclimate.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/codeclimate.toml>`_:

.. code-block:: toml

    # https://codeclimate.com/
    # https://docs.codeclimate.com/docs/maintainability#section-checks
    # https://docs.codeclimate.com/docs/advanced-configuration#default-checks
    [".codeclimate.yml"]
    version = "2"

    [".codeclimate.yml".checks.file-lines.config]
    # Pylint's default is also 1000: https://github.com/PyCQA/pylint/blob/master/pylint/checkers/format.py#L294-L300
    threshold = 1000

    [".codeclimate.yml".checks.method-complexity.config]
    threshold = 10  # Same as [flake8]max-complexity

    [".codeclimate.yml".plugins.fixme]  # https://docs.codeclimate.com/docs/fixme
    # https://github.com/codeclimate/codeclimate-fixme
    enabled = false

.. _example-commitizen:

commitizen_
-----------

Contents of `resources/any/commitizen.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/commitizen.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/commitizen-tools/commitizen"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "commitizen"
    stages = ["commit-msg"]

.. _example-commitlint:

commitlint_
-----------

Contents of `resources/any/commitlint.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/commitlint.toml>`_:

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
    repo = "https://github.com/alessandrojcm/commitlint-pre-commit-hook"

    [[".pre-commit-config.yaml".repos.hooks]]
    additional_dependencies = ["@commitlint/config-conventional"]
    id = "commitlint"
    stages = ["commit-msg"]

.. _example-editorconfig:

EditorConfig_
-------------

Contents of `resources/any/editorconfig.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/editorconfig.toml>`_:

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

    [".codeclimate.yml".plugins.editorconfig]  # https://docs.codeclimate.com/docs/editorconfig
    enabled = true

.. _example-git-legal:

git-legal_
----------

Contents of `resources/any/git-legal.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/git-legal.toml>`_:

.. code-block:: toml

    [".codeclimate.yml".plugins.git-legal]  # https://docs.codeclimate.com/docs/git-legal
    enabled = true

.. _example-pre-commit-hooks-for-any-language:

pre-commit_ hooks for any language
----------------------------------

Contents of `resources/any/hooks.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/hooks.toml>`_:

.. code-block:: toml

    # See https://pre-commit.com for more information
    # See https://pre-commit.com/hooks.html for more hooks

    [nitpick.files.present]
    ".pre-commit-config.yaml" = "Create the file with the contents below, then run 'pre-commit install'"

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/pre-commit/pre-commit-hooks"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "end-of-file-fixer"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "trailing-whitespace"

.. _example-markdownlint:

markdownlint_
-------------

Contents of `resources/any/markdownlint.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/markdownlint.toml>`_:

.. code-block:: toml

    [".codeclimate.yml".plugins.markdownlint]  # https://docs.codeclimate.com/docs/markdownlint # TODO: enable it after configuring a style
    # https://github.com/markdownlint/markdownlint
    enabled = false

.. _example-prettier:

Prettier_
---------

Contents of `resources/any/prettier.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/any/prettier.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/pre-commit/mirrors-prettier"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "prettier"
    stages = ["commit"]

.. _example-package-json:

package.json_
-------------

Contents of `resources/javascript/package-json.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/javascript/package-json.toml>`_:

.. code-block:: toml

    ["package.json"]
    contains_keys = ["name", "version", "repository.type", "repository.url", "release.plugins"]

.. _example-python-3-10:

Python 3.10
-----------

Contents of `resources/python/310.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/310.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.10"

.. _example-python-3-6:

Python 3.6
----------

Contents of `resources/python/36.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/36.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.6.1"

.. _example-python-3-7:

Python 3.7
----------

Contents of `resources/python/37.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/37.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.7"

.. _example-python-3-8:

Python 3.8
----------

Contents of `resources/python/38.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/38.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.8"

.. _example-python-3-9:

Python 3.9
----------

Contents of `resources/python/39.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/39.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    python = "^3.9"

.. _example-absent-files:

Absent files
------------

Contents of `resources/python/absent.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/absent.toml>`_:

.. code-block:: toml

    [nitpick.files.absent]
    "requirements.txt" = "Install poetry, run 'poetry init' to create pyproject.toml, and move dependencies to it"
    ".isort.cfg" = "Move values to setup.cfg, section [isort]"
    "Pipfile" = "Use pyproject.toml instead"
    "Pipfile.lock" = "Use pyproject.toml instead"
    ".venv" = ""
    ".pyup.yml" = "Configure safety instead: https://github.com/pyupio/safety#using-safety-with-a-ci-service"

.. _example-autoflake:

autoflake_
----------

Contents of `resources/python/autoflake.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/autoflake.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/myint/autoflake"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "autoflake"
    args = ["--in-place", "--remove-all-unused-imports", "--remove-unused-variables", "--remove-duplicate-keys", "--ignore-init-module-imports"]

.. _example-bandit:

bandit_
-------

Contents of `resources/python/bandit.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/bandit.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/PyCQA/bandit"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "bandit"
    args = ["--ini", "setup.cfg"]
    exclude = "tests/"

    [".codeclimate.yml".plugins.bandit]  # https://docs.codeclimate.com/docs/bandit
    # https://github.com/PyCQA/bandit
    enabled = true

.. _example-black:

black_
------

Contents of `resources/python/black.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/black.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.black]
    line-length = 120

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/psf/black"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "black"
    args = ["--safe", "--quiet"]

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/asottile/blacken-docs"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "blacken-docs"
    additional_dependencies = ["black==21.5b2"]

.. _example-flake8:

flake8_
-------

Contents of `resources/python/flake8.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/flake8.toml>`_:

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
    repo = "https://github.com/PyCQA/flake8"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "flake8"
    additional_dependencies = ["flake8-blind-except", "flake8-bugbear", "flake8-comprehensions", "flake8-debugger", "flake8-docstrings", "flake8-isort", "flake8-polyfill", "flake8-pytest", "flake8-quotes", "flake8-typing-imports", "yesqa"]

    [".codeclimate.yml".plugins.pep8]  # https://docs.codeclimate.com/docs/pep8 PEP8 already being checked by flake8 plugins on pre-commit
    enabled = false

.. _example-github-workflow-python:

GitHub Workflow (Python)
------------------------

Contents of `resources/python/github-workflow.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/github-workflow.toml>`_:

.. code-block:: toml

    [".github/workflows/python.yaml"]
    name = "Python"
    on = ["push", "pull_request"]

    [".github/workflows/python.yaml".jobs.build.strategy]
    fail-fast = false

    [".github/workflows/python.yaml".jobs.build.strategy.matrix]
    os = ["ubuntu-latest", "windows-latest", "macos-latest"]
    python-version = ["3.6", "3.7", "3.8", "3.9", "3.10"]

    [".github/workflows/python.yaml".jobs.build]
    name = "${{ matrix.python-version }} ${{ matrix.os }}"
    runs-on = "${{ matrix.os }}"

    [".github/workflows/python.yaml".jobs.build.env]
    PYTHONUNBUFFERED = 1

    [[".github/workflows/python.yaml".jobs.build.steps]]
    name = "Checkout"
    uses = "actions/checkout@v2"

    [[".github/workflows/python.yaml".jobs.build.steps]]
    name = "Set up Python ${{ matrix.python-version }}"
    uses = "actions/setup-python@v2"

    [".github/workflows/python.yaml".jobs.build.steps.with]
    python-version = "${{ matrix.python-version }}"

    [[".github/workflows/python.yaml".jobs.build.steps]]
    name = "Install tox"
    run = "python -m pip install tox"

.. _example-pre-commit-hooks-for-python:

pre-commit_ hooks for Python
----------------------------

Contents of `resources/python/hooks.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/hooks.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/pre-commit/pygrep-hooks"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "python-check-blanket-noqa"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "python-check-mock-methods"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "python-no-eval"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "python-no-log-warn"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "rst-backticks"

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/pre-commit/pre-commit-hooks"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "debug-statements"

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/asottile/pyupgrade"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "pyupgrade"

.. _example-ipython:

IPython_
--------

Contents of `resources/python/ipython.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/ipython.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dev-dependencies]
    ipython = "*"
    ipdb = "*"

.. _example-isort:

isort_
------

Contents of `resources/python/isort.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/isort.toml>`_:

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
    repo = "https://github.com/PyCQA/isort"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "isort"

.. _example-mypy:

mypy_
-----

Contents of `resources/python/mypy.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/mypy.toml>`_:

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
    # False positives when running on local machine... it works on pre-commit.ci ¯\_(ツ)_/¯
    warn_unused_ignores = false

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/pre-commit/mirrors-mypy"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "mypy"
    args = ["--show-error-codes"]

.. _example-poetry:

Poetry_
-------

Contents of `resources/python/poetry.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/poetry.toml>`_:

.. code-block:: toml

    [nitpick.files.present]
    "pyproject.toml" = "Install poetry and run 'poetry init' to create it"

.. _example-pylint:

Pylint_
-------

Contents of `resources/python/pylint.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/pylint.toml>`_:

.. code-block:: toml

    ["pyproject.toml".tool.poetry.dependencies]
    pylint = {version = "*", optional = true}

    ["pyproject.toml".tool.poetry.extras]
    lint = ["pylint"]

    # pylint needs to be installed in the same venv as the project, to be more useful
    # https://github.com/pre-commit/mirrors-pylint#using-pylint-with-pre-commit
    [[".pre-commit-config.yaml".repos]]
    repo = "local"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "pylint"
    name = "pylint"
    language = "system"
    exclude = "tests/"
    types = ["python"]

    [".pylintrc".MASTER]
    # Use multiple processes to speed up Pylint.
    jobs = 1

    # https://github.com/samuelcolvin/pydantic/issues/1961#issuecomment-759522422
    extension-pkg-whitelist = "pydantic"

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
    #disable = "bad-continuation,bad-whitespace,fixme,cyclic-import,line-too-long"

    [".pylintrc".BASIC]
    # List of builtins function names that should not be used, separated by a comma
    bad-functions = "map,filter"
    # Good variable names which should always be accepted, separated by a comma
    good-names = "i,j,k,e,ex,Run,_,id,rv,c"

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

    [".codeclimate.yml".plugins.pylint]  # https://docs.codeclimate.com/docs/pylint Already checked by pre-commit
    enabled = false

.. _example-radon:

radon_
------

Contents of `resources/python/radon.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/radon.toml>`_:

.. code-block:: toml

    [".codeclimate.yml".plugins.radon]  # https://docs.codeclimate.com/docs/radon
    enabled = true
    [".codeclimate.yml".plugins.radon.config]
    # https://radon.readthedocs.io/en/latest/commandline.html#the-cc-command
    threshold = "C"

.. _example-readthedocs:

ReadTheDocs_
------------

Contents of `resources/python/readthedocs.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/readthedocs.toml>`_:

.. code-block:: toml

    # https://docs.readthedocs.io/en/stable/config-file/v2.html
    [".readthedocs.yml"]
    version = 2
    formats = "all"

    [".readthedocs.yml".sphinx]
    configuration = "docs/conf.py"

    [[".readthedocs.yml".python.install]]
    method = "pip"
    path = "."
    extra_requirements = ["doc"]

.. _example-sonar-python:

sonar-python_
-------------

Contents of `resources/python/sonar-python.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/sonar-python.toml>`_:

.. code-block:: toml

    [".codeclimate.yml".plugins.sonar-python]  # https://docs.codeclimate.com/docs/sonar-python
    # https://github.com/SonarSource/sonar-python
    enabled = true

.. _example-python-stable-version:

Python (stable version)
-----------------------

Contents of `resources/python/stable.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/stable.toml>`_:

.. code-block:: toml

    [".readthedocs.yml".python]
    # ReadTheDocs still didn't upgrade to Python 3.9:
    # Problem in your project's configuration. Invalid "python.version":
    # expected one of (2, 2.7, 3, 3.5, 3.6, 3.7, 3.8, pypy3.5), got 3.9
    version = "3.8"

.. _example-tox:

tox_
----

Contents of `resources/python/tox.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/python/tox.toml>`_:

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

.. _example-bashate:

bashate_
--------

Contents of `resources/shell/bashate.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/shell/bashate.toml>`_:

.. code-block:: toml

    [[".pre-commit-config.yaml".repos]]
    repo = "https://github.com/openstack/bashate"

    [[".pre-commit-config.yaml".repos.hooks]]
    id = "bashate"

    # https://docs.openstack.org/bashate/latest/man/bashate.html#options
    args = ["-i", "E006"]

.. _example-shellcheck:

shellcheck_
-----------

Contents of `resources/shell/shellcheck.toml <https://github.com/andreoliwa/nitpick/blob/v0.30.0/resources/shell/shellcheck.toml>`_:

.. code-block:: toml

    [".codeclimate.yml".plugins.shellcheck]  # https://docs.codeclimate.com/docs/shellcheck
    # https://github.com/koalaman/shellcheck
    enabled = true
