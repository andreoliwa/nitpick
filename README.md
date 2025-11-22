# Nitpick

[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.org/project/nitpick)
[![Supported Python
versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)
![GitHub Actions Python
Workflow](https://github.com/andreoliwa/nitpick/workflows/Python/badge.svg)
[![Documentation
Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.rtfd.io/en/latest/?badge=latest)
[![Codecov](https://codecov.io/gh/andreoliwa/nitpick/branch/master/graph/badge.svg)](https://codecov.io/gh/andreoliwa/nitpick)
[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick)
[![Test
Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pre-commit.ci
status](https://results.pre-commit.ci/badge/github/andreoliwa/nitpick/develop.svg)](https://results.pre-commit.ci/latest/github/andreoliwa/nitpick/develop)
[![Project
License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Code style:
black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com/)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![FOSSA
Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fandreoliwa%2Fnitpick?ref=badge_shield)

Command-line tool and [flake8](https://github.com/PyCQA/flake8) plugin
to enforce the same settings across multiple language-independent
projects.

Useful if you maintain multiple projects and are tired of
copying/pasting the same INI/TOML/YAML/JSON keys and values over and
over, in all of them.

The CLI now has a `nitpick fix` command that modifies configuration
files directly (pretty much like [black](https://github.com/psf/black)
and [isort](https://github.com/PyCQA/isort) do with Python files). See
the [CLI docs for more
info](https://nitpick.rtfd.io/en/latest/cli.html).

Many more features are planned for the future, check [the
roadmap](https://github.com/andreoliwa/nitpick/projects/1).

## The style file

A "Nitpick code style" is a [TOML](https://github.com/toml-lang/toml)
file with the settings that should be present in config files from other
tools.

Example of a style:

``` toml
["pyproject.toml".tool.black]
line-length = 120

["pyproject.toml".tool.poetry.group.dev.dependencies]
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
```

This style will assert that:

- ... [black](https://github.com/psf/black),
  [isort](https://github.com/PyCQA/isort) and
  [flake8](https://github.com/PyCQA/flake8) have a line length of 120;
- ... [flake8](https://github.com/PyCQA/flake8) and
  [isort](https://github.com/PyCQA/isort) are configured as above in
  `setup.cfg`;
- ... [Pylint](https://www.pylint.org) is present as a
  [Poetry](https://github.com/python-poetry/poetry) dev dependency in
  `pyproject.toml`.

## Supported file types

These are the file types currently handled by Nitpick.

- Some files are only being checked and have to be modified manually;
- Some files can already be fixed automatically (with the `nitpick fix`
  command);
- Others are still under construction; the ticket numbers are shown in
  the table (upvote the ticket with 👍🏻 if you would like to prioritise
  development).

### Implemented

<!-- auto-generated-start-implemented -->
| File type | `nitpick check` | `nitpick fix` |
| --- | --- | --- |
| `Any INI file <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_ | ✅ | ✅ |
| `Any JSON file <https://nitpick.rtfd.io/en/latest/plugins.html#json-files>`_ | ✅ | ✅ |
| `Any plain text file <https://nitpick.rtfd.io/en/latest/plugins.html#text-files>`_ | ✅ | ❌ |
| `Any TOML file <https://nitpick.rtfd.io/en/latest/plugins.html#toml-files>`_ | ✅ | ✅ |
| `Any YAML file <https://nitpick.rtfd.io/en/latest/plugins.html#yaml-files>`_ | ✅ | ✅ |
| `.editorconfig <https://nitpick.rtfd.io/en/latest/library.html#any>`_ | ✅ | ✅ |
| `.pylintrc <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_ | ✅ | ✅ |
| `setup.cfg <https://nitpick.rtfd.io/en/latest/plugins.html#ini-files>`_ | ✅ | ✅ |
<!-- auto-generated-end-implemented -->

### Planned

<!-- auto-generated-start-planned -->
| File type | `nitpick check` | `nitpick fix` |
| --- | --- | --- |
| Any Markdown file | `#280 <https://github.com/andreoliwa/nitpick/issues/280>`_ 🚧 | ❓ |
| Any Terraform file | `#318 <https://github.com/andreoliwa/nitpick/issues/318>`_ 🚧 | ❓ |
| Dockerfile | `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧 | `#272 <https://github.com/andreoliwa/nitpick/issues/272>`_ 🚧 |
| .dockerignore | `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧 | `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧 |
| .gitignore | `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧 | `#8 <https://github.com/andreoliwa/nitpick/issues/8>`_ 🚧 |
| Jenkinsfile | `#278 <https://github.com/andreoliwa/nitpick/issues/278>`_ 🚧 | ❓ |
| Makefile | `#277 <https://github.com/andreoliwa/nitpick/issues/277>`_ 🚧 | ❓ |
<!-- auto-generated-end-planned -->

## Style Library (Presets)

Nitpick has a builtin library of style presets, shipped as [Python
resources](https://docs.python.org/3/library/importlib.html#module-importlib.resources).

This library contains building blocks for your your custom style. Just
choose styles from the table below and create your own style, like LEGO.

Read how to:

- [...add multiple styles to the configuration
  file](https://nitpick.readthedocs.io/en/latest/configuration.html#multiple-styles);
- [...include styles inside a
  style](https://nitpick.readthedocs.io/en/latest/nitpick_section.html#nitpick-styles).

<!-- auto-generated-start-style-library -->

## any

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/any/codeclimate](src/nitpick/resources/any/codeclimate.toml) | [CodeClimate](https://codeclimate.com/) |
| [py://nitpick/resources/any/commitizen](src/nitpick/resources/any/commitizen.toml) | [Commitizen (Python)](https://github.com/commitizen-tools/commitizen) |
| [py://nitpick/resources/any/commitlint](src/nitpick/resources/any/commitlint.toml) | [commitlint](https://github.com/conventional-changelog/commitlint) |
| [py://nitpick/resources/any/editorconfig](src/nitpick/resources/any/editorconfig.toml) | [EditorConfig](https://editorconfig.org/) |
| [py://nitpick/resources/any/git-legal](src/nitpick/resources/any/git-legal.toml) | [Git.legal - CodeClimate Community Edition](https://github.com/kmewhort/git.legal-codeclimate) |
| [py://nitpick/resources/any/pre-commit-hooks](src/nitpick/resources/any/pre-commit-hooks.toml) | [pre-commit hooks for any project](https://github.com/pre-commit/pre-commit-hooks) |
| [py://nitpick/resources/any/prettier](src/nitpick/resources/any/prettier.toml) | [Prettier](https://github.com/prettier/prettier) |

## javascript

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/javascript/package-json](src/nitpick/resources/javascript/package-json.toml) | [package.json](https://github.com/yarnpkg/website/blob/master/lang/en/docs/package-json.md) |

## kotlin

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/kotlin/ktlint](src/nitpick/resources/kotlin/ktlint.toml) | [ktlint](https://github.com/pinterest/ktlint) |

## markdown

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/markdown/markdownlint](src/nitpick/resources/markdown/markdownlint.toml) | [Markdown lint](https://github.com/markdownlint/markdownlint) |

## presets

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/presets/nitpick](src/nitpick/resources/presets/nitpick.toml) | [Default style file for Nitpick](https://nitpick.rtfd.io/) |

## proto

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/proto/protolint](src/nitpick/resources/proto/protolint.toml) | [protolint (Protobuf linter)](https://github.com/yoheimuta/protolint) |

## python

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/python/310](src/nitpick/resources/python/310.toml) | Python 3.10 |
| [py://nitpick/resources/python/311](src/nitpick/resources/python/311.toml) | Python 3.11 |
| [py://nitpick/resources/python/312](src/nitpick/resources/python/312.toml) | Python 3.12 |
| [py://nitpick/resources/python/313](src/nitpick/resources/python/313.toml) | Python 3.13 |
| [py://nitpick/resources/python/314](src/nitpick/resources/python/314.toml) | Python 3.14 |
| [py://nitpick/resources/python/absent](src/nitpick/resources/python/absent.toml) | Files that should not exist |
| [py://nitpick/resources/python/autoflake](src/nitpick/resources/python/autoflake.toml) | [autoflake](https://github.com/myint/autoflake) |
| [py://nitpick/resources/python/bandit](src/nitpick/resources/python/bandit.toml) | [Bandit](https://github.com/PyCQA/bandit) |
| [py://nitpick/resources/python/black](src/nitpick/resources/python/black.toml) | [Black](https://github.com/psf/black) |
| [py://nitpick/resources/python/flake8](src/nitpick/resources/python/flake8.toml) | [Flake8](https://github.com/PyCQA/flake8) |
| [py://nitpick/resources/python/github-workflow](src/nitpick/resources/python/github-workflow.toml) | [GitHub Workflow for Python](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions) |
| [py://nitpick/resources/python/ipython](src/nitpick/resources/python/ipython.toml) | [IPython](https://github.com/ipython/ipython) |
| [py://nitpick/resources/python/isort](src/nitpick/resources/python/isort.toml) | [isort](https://github.com/PyCQA/isort) |
| [py://nitpick/resources/python/mypy](src/nitpick/resources/python/mypy.toml) | [Mypy](https://github.com/python/mypy) |
| [py://nitpick/resources/python/poetry-editable](src/nitpick/resources/python/poetry-editable.toml) | [Poetry (editable projects; PEP 600 support)](https://github.com/python-poetry/poetry) |
| [py://nitpick/resources/python/poetry-venv](src/nitpick/resources/python/poetry-venv.toml) | [Poetry (virtualenv in project)](https://github.com/python-poetry/poetry) |
| [py://nitpick/resources/python/poetry](src/nitpick/resources/python/poetry.toml) | [Poetry](https://github.com/python-poetry/poetry) |
| [py://nitpick/resources/python/pre-commit-hooks](src/nitpick/resources/python/pre-commit-hooks.toml) | [pre-commit hooks for Python projects](https://pre-commit.com/hooks) |
| [py://nitpick/resources/python/pylint](src/nitpick/resources/python/pylint.toml) | [Pylint](https://github.com/PyCQA/pylint) |
| [py://nitpick/resources/python/radon](src/nitpick/resources/python/radon.toml) | [Radon](https://github.com/rubik/radon) |
| [py://nitpick/resources/python/readthedocs](src/nitpick/resources/python/readthedocs.toml) | [Read the Docs](https://github.com/readthedocs/readthedocs.org) |
| [py://nitpick/resources/python/sonar-python](src/nitpick/resources/python/sonar-python.toml) | [SonarQube Python plugin](https://github.com/SonarSource/sonar-python) |
| [py://nitpick/resources/python/tox](src/nitpick/resources/python/tox.toml) | [tox](https://github.com/tox-dev/tox) |

## shell

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/shell/bashate](src/nitpick/resources/shell/bashate.toml) | [bashate (code style for Bash)](https://github.com/openstack/bashate) |
| [py://nitpick/resources/shell/shellcheck](src/nitpick/resources/shell/shellcheck.toml) | [ShellCheck (static analysis for shell scripts)](https://github.com/koalaman/shellcheck) |
| [py://nitpick/resources/shell/shfmt](src/nitpick/resources/shell/shfmt.toml) | [shfmt (shell script formatter)](https://github.com/mvdan/sh) |

## toml

| Style URL | Description |
| --- | --- |
| [py://nitpick/resources/toml/toml-sort](src/nitpick/resources/toml/toml-sort.toml) | [TOML sort](https://github.com/pappasam/toml-sort) |
<!-- auto-generated-end-style-library -->

## Quickstart

### Install

Install in an isolated global environment with
[pipx](https://github.com/pipxproject/pipx):

    # Latest PyPI release
    pipx install nitpick

    # Development branch from GitHub
    pipx install git+https://github.com/andreoliwa/nitpick

On macOS/Linux, install with
[Homebrew](https://github.com/Homebrew/brew):

    # Latest PyPI release
    brew install andreoliwa/formulae/nitpick

    # Development branch from GitHub
    brew install andreoliwa/formulae/nitpick --HEAD

On Arch Linux, install with yay:

    yay -Syu nitpick

Add to your project with [uv](https://docs.astral.sh/uv/):

    uv add --dev nitpick

Or install it with pip:

    pip install -U nitpick

### Run

[Nitpick](#nitpick) will fail if no style is explicitly configured. Run
this command to download and use the opinionated [default style
file](nitpick-style.toml):

> nitpick init

You can use it as a template to configure your own style.

To fix and modify your files directly:

    nitpick fix

To check for errors only:

    nitpick check

Nitpick is also a [flake8](https://github.com/PyCQA/flake8) plugin, so
you can run this on a project with at least one Python (`.py`) file:

    flake8 .

### Run as a pre-commit hook

If you use [pre-commit](https://pre-commit.com/) on your project, add
this to the `.pre-commit-config.yaml` in your repository:

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.38.0
        hooks:
          - id: nitpick-suggest
          - id: nitpick

There are a few hook IDs available:

- `nitpick`, `nitpick-fix` and `nitpick-fix-all` run the `nitpick fix`
  command;
- `nitpick-check` and `nitpick-check-all` runs `nitpick check`;
- `nitpick-suggest` runs `nitpick init --fix --suggest`;

If you want to run Nitpick as a flake8 plugin instead:

    repos:
      - repo: https://github.com/PyCQA/flake8
        rev: 4.0.1
        hooks:
          - id: flake8
            additional_dependencies: [nitpick]

### Run as a MegaLinter plugin

If you use [MegaLinter](https://megalinter.github.io/) you can run
Nitpick as a plugin. Add the following two entries to your
`.mega-linter.yml` configuration file:

``` yaml
PLUGINS:
  - https://raw.githubusercontent.com/andreoliwa/nitpick/v0.38.0/mega-linter-plugin-nitpick/nitpick.megalinter-descriptor.yml
ENABLE_LINTERS:
  - NITPICK
```

## More information

Nitpick is being used by projects such as:

- [wemake-services/wemake-python-styleguide](https://github.com/wemake-services/wemake-python-styleguide)
- [dry-python/returns](https://github.com/dry-python/returns)
- [sobolevn/django-split-settings](https://github.com/sobolevn/django-split-settings)
- [catalyst-team/catalyst](https://github.com/catalyst-team/catalyst)
- [alan-turing-institute/AutSPACEs](https://github.com/alan-turing-institute/AutSPACEs)
- [pytest-dev/pytest-mimesis](https://github.com/pytest-dev/pytest-mimesis)

For more details on styles and which configuration files are currently
supported, [see the full documentation](https://nitpick.rtfd.io/).

## Contributing

Your help is very much appreciated.

There are many possibilities for new features in this project, and not
enough time or hands to work on them.

If you want to contribute with the project, set up your development
environment following the steps on the [contribution
guidelines](https://nitpick.rtfd.io/en/latest/contributing.html) and
send your pull request.
