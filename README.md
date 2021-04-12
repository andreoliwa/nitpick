# Nitpick

[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.org/project/nitpick)
![GitHub Actions Python Workflow](https://github.com/andreoliwa/nitpick/workflows/Python/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.rtfd.io/en/latest/?badge=latest)
[![Coveralls](https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg)](https://coveralls.io/github/andreoliwa/nitpick)
[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick)
[![Test Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Project License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com/)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/andreoliwa/nitpick/develop.svg)](https://results.pre-commit.ci/latest/github/andreoliwa/nitpick/develop)

Command-line tool and [flake8](https://github.com/PyCQA/flake8) plugin to enforce the same settings across multiple language-independent projects.

Useful if you maintain multiple projects and are tired of copying/pasting the same INI/TOML/YAML/JSON keys and values over and over, in all of them.

The tool now has an "apply" feature that modifies configuration files directly (pretty much like [black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort) do with Python files).
See the [CLI docs for more info](https://nitpick.rtfd.io/en/latest/cli.html).

Many more features are planned for the future, check [the roadmap](https://github.com/andreoliwa/nitpick/projects/1).

## Style file

A "nitpick code style" is a [TOML](https://github.com/toml-lang/toml) file with the settings that should be present in config files from other tools.

Example of a style:

```
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
```

This style will assert that:

- ... [black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and [flake8](https://github.com/PyCQA/flake8) have a line length of 120;
- ... [flake8](https://github.com/PyCQA/flake8) and [isort](https://github.com/PyCQA/isort) are configured as above in `setup.cfg`;
- ... [Pylint](https://www.pylint.org) is present as a [Poetry](https://github.com/python-poetry/poetry) dev dependency in `pyproject.toml`).

## Supported file types

These are the file types currently handled by Nitpick.

- Some files are only being checked and have to be modified manually;
- Some files can already be fixed automatically (with the [`nitpick run`](#run) command);
- Others are still under construction; the ticket numbers are shown in the table (upvote the ticket with 👍🏻 if you would like to prioritise development).

### Implemented

| File type                                                                                          | Check | Fix ([`nitpick run`](#run))                                            |
| -------------------------------------------------------------------------------------------------- | ----- | ---------------------------------------------------------------------- |
| [Any `.ini` file](https://nitpick.rtfd.io/en/latest/plugins.html#ini-files)                        | ✅    | ✅                                                                     |
| [Any `.json` file](https://nitpick.rtfd.io/en/latest/plugins.html#json-files)                      | ✅    | ❌                                                                     |
| [Any text file](https://nitpick.rtfd.io/en/latest/plugins.html#text-files)                         | ✅    | ❌                                                                     |
| [`.editorconfig`](https://nitpick.rtfd.io/en/latest/examples.html#example-editorconfig)            | ✅    | ✅                                                                     |
| [`.pre-commit-config.yaml`](https://nitpick.rtfd.io/en/latest/plugins.html#pre-commit-config-yaml) | ✅    | 🚧&nbsp;&nbsp;[#282](https://github.com/andreoliwa/nitpick/issues/282) |
| [`.pylintrc`](https://nitpick.rtfd.io/en/latest/plugins.html#ini-files)                            | ✅    | ✅                                                                     |
| [`package.json`](https://nitpick.rtfd.io/en/latest/examples.html#example-package-json)             | ✅    | ❌                                                                     |
| [`pyproject.toml`](https://nitpick.rtfd.io/en/latest/plugins.html#pyproject-toml)                  | ✅    | ✅                                                                     |
| [`requirements.txt`](https://nitpick.rtfd.io/en/latest/plugins.html#text-files)                    | ✅    | ❌                                                                     |
| [`setup.cfg`](https://nitpick.rtfd.io/en/latest/plugins.html#ini-files)                            | ✅    | ✅                                                                     |

### Planned

| File type                  | Check                                                                  | Fix ([`nitpick run`](#run))                                            |
| -------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Any `.md` (Markdown) file  | 🚧&nbsp;&nbsp;[#280](https://github.com/andreoliwa/nitpick/issues/280) | ❓                                                                     |
| Any `.tf` (Terraform) file | 🚧&nbsp;&nbsp;[#318](https://github.com/andreoliwa/nitpick/issues/318) | ❓                                                                     |
| Any `.toml` file           | 🚧&nbsp;&nbsp;[#320](https://github.com/andreoliwa/nitpick/issues/320) | 🚧&nbsp;&nbsp;[#320](https://github.com/andreoliwa/nitpick/issues/320) |
| `.dockerignore`            | 🚧&nbsp;&nbsp;[#8](https://github.com/andreoliwa/nitpick/issues/8)     | 🚧&nbsp;&nbsp;[#8](https://github.com/andreoliwa/nitpick/issues/8)     |
| `.gitignore`               | 🚧&nbsp;&nbsp;[#8](https://github.com/andreoliwa/nitpick/issues/8)     | 🚧&nbsp;&nbsp;[#8](https://github.com/andreoliwa/nitpick/issues/8)     |
| `.travis.yml`              | 🚧&nbsp;&nbsp;[#15](https://github.com/andreoliwa/nitpick/issues/15)   | 🚧&nbsp;&nbsp;[#15](https://github.com/andreoliwa/nitpick/issues/15)   |
| `Dockerfile`               | 🚧&nbsp;&nbsp;[#272](https://github.com/andreoliwa/nitpick/issues/272) | 🚧&nbsp;&nbsp;[#272](https://github.com/andreoliwa/nitpick/issues/272) |
| `Jenkinsfile`              | 🚧&nbsp;&nbsp;[#278](https://github.com/andreoliwa/nitpick/issues/278) | ❓                                                                     |
| `Makefile`                 | 🚧&nbsp;&nbsp;[#277](https://github.com/andreoliwa/nitpick/issues/277) | ❓                                                                     |

## Quick setup

### Install

On macOS, install the latest release with [Homebrew](https://github.com/Homebrew/brew):

    brew install andreoliwa/formulae/nitpick

    # To install the latest version from the `develop` branch:
    brew install andreoliwa/formulae/nitpick --HEAD

On archlinux, install with yay:

    yay -Syu nitpick

Add to your project with [Poetry](https://github.com/python-poetry/poetry):

    poetry add --dev nitpick

Or install it with pip:

    pip install -U nitpick

### Run

To fix and modify your files directly:

    nitpick run

To check for errors only:

    nitpick run --check

Nitpick is also a `flake8` plugin, so you can run this on a project with at least one Python (`.py`) file:

    flake8 .

Nitpick will download and use the opinionated [default style file](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.26.0/nitpick-style.toml).

You can use it as a template to configure your own style.

### Run as a pre-commit hook (recommended)

If you use [pre-commit](https://pre-commit.com/) on your project (you should), add this to the `.pre-commit-config.yaml` in your repository:

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.26.0
        hooks:
          - id: nitpick

To install the `pre-commit` and `commit-msg` Git hooks:

    pre-commit install --install-hooks
    pre-commit install -t commit-msg

To start checking all your code against the default rules:

    pre-commit run --all-files

## More information

For more details on styles and which configuration files are currently supported, [see the full documentation](https://nitpick.rtfd.io/).
