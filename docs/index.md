# Nitpick

[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.org/project/nitpick/)
[![GitHub Workflow](https://github.com/andreoliwa/nitpick/actions/workflows/python.yaml/badge.svg)](https://github.com/andreoliwa/nitpick/actions/workflows/python.yaml)
[![Documentation Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.rtfd.io/latest/?badge=latest)
[![Codecov](https://codecov.io/gh/andreoliwa/nitpick/branch/master/graph/badge.svg)](https://codecov.io/gh/andreoliwa/nitpick)
[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick)
[![Test Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Project License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)

Command-line tool and [flake8](https://github.com/PyCQA/flake8) plugin to enforce the same settings across multiple language-independent projects.

Useful if you maintain multiple projects and are tired of copying/pasting the same INI/TOML/YAML/JSON keys and values over and over, in all of them.

The CLI now has a `nitpick fix` command that modifies configuration files directly (pretty much like [black](https://github.com/psf/black) and [isort](https://github.com/PyCQA/isort) do with Python files). See the [CLI documentation](cli.md) for more info.

Many more features are planned for the future, check [the roadmap](https://github.com/andreoliwa/nitpick/projects/1).

!!! note

    This project is still a work in progress, so the API is not fully defined:

    - The style file syntax might have changes before the 1.0 stable release
    - The numbers in the `NIP*` error codes might change; don't fully rely on them
    - See also the breaking changes section
