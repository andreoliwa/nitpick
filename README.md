# nitpick

[![PyPI](https://img.shields.io/pypi/v/nitpick.svg)](https://pypi.python.org/pypi/nitpick)
[![Travis CI](https://travis-ci.com/andreoliwa/nitpick.svg)](https://travis-ci.com/andreoliwa/nitpick)
[![Documentation Status](https://readthedocs.org/projects/nitpick/badge/?version=latest)](https://nitpick.readthedocs.io/en/latest/?badge=latest)
[![Coveralls](https://coveralls.io/repos/github/andreoliwa/nitpick/badge.svg)](https://coveralls.io/github/andreoliwa/nitpick)
[![Maintainability](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/maintainability)](https://codeclimate.com/github/andreoliwa/nitpick/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/61e0cdc48e24e76a0460/test_coverage)](https://codeclimate.com/github/andreoliwa/nitpick/test_coverage)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Project License](https://img.shields.io/pypi/l/nitpick.svg)](https://pypi.org/project/nitpick/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=andreoliwa/nitpick)](https://dependabot.com)
[![semantic-release](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--release-e10079.svg)](https://github.com/semantic-release/semantic-release)

Flake8 plugin to enforce the same lint configuration (flake8, isort, mypy, pylint) across multiple Python projects.

A "nitpick code style" is a [TOML](https://github.com/toml-lang/toml) file with settings that should be present in config files from other tools. E.g.:

- `pyproject.toml` and `setup.cfg` (used by [flake8](http://flake8.pycqa.org/), [black](https://black.readthedocs.io/), [isort](https://isort.readthedocs.io/), [mypy](https://mypy.readthedocs.io/));
- `.pylintrc` (used by [pylint](https://pylint.readthedocs.io/) config);
- more files to come.

---

- [Installation and usage](#installation-and-usage)
- [Style file](#style-file)
- [setup.cfg](#setupcfg)

---

## Installation and usage

To try the package, simply install it (in a virtualenv or globally, wherever) and run `flake8`:

    $ pip install -U nitpick
    $ flake8

You will see warnings if your project configuration is different than [the default style file](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.19.0/nitpick-style.toml).

### As a pre-commit hook

If you use [pre-commit](https://pre-commit.com/) on your project, add this to the `.pre-commit-config.yaml` in your repository:

    repos:
      - repo: https://github.com/andreoliwa/nitpick
        rev: v0.19.0
        hooks:
          # Run nitpick and several other flake8 plugins
          - id: nitpick-all
          # Check only nitpick errors, ignore other flake8 plugins
          - id: nitpick-only

Use one hook or the other (`nitpick-all` **or** `nitpick-only`), not both.
To check all the other flake8 plugins that are installed with `nitpick`, see the [pyproject.toml](pyproject.toml).

## Style file

### Configure your own style file

Change your project config on `pyproject.toml`, and configure your own style like this:

    [tool.nitpick]
    style = "https://raw.githubusercontent.com/andreoliwa/nitpick/v0.19.0/nitpick-style.toml"

You can set `style` with any local file or URL. E.g.: you can use the raw URL of a [GitHub Gist](https://gist.github.com).

You can also use multiple styles and mix local files and URLs:

    [tool.nitpick]
    style = ["/path/to/first.toml", "/another/path/to/second.toml", "https://example.com/on/the/web/third.toml"]

The order is important: each style will override any keys that might be set by the previous .toml file.
If a key is defined in more than one file, the value from the last file will prevail.

### Default search order for a style file

1. A file or URL configured in the `pyproject.toml` file, `[tool.nitpick]` section, `style` key, as [described above](#configure-your-own-style-file).

2. Any `nitpick-style.toml` file found in the current directory (the one in which `flake8` runs from) or above.

3. If no style is found, then [the default style file from GitHub](https://raw.githubusercontent.com/andreoliwa/nitpick/v0.19.0/nitpick-style.toml) is used.

### Style file syntax

NOTE: The project is still experimental; the style file syntax might slightly change before the 1.0 stable release.

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To [configure the black formatter](https://github.com/python/black#configuration-format) with a line length of 120, you use this in your `pyproject.toml`:

    [tool.black]
    line-length = 120

To enforce that all your projects use this same line length, add this to your `nitpick-style.toml` file:

    ["pyproject.toml".tool.black]
    line-length = 120

It's the same exact section/key, just prefixed with the config file name (`"pyproject.toml".`)

The same works for `setup.cfg`.
To [configure mypy](https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format) to ignore missing imports in your project:

    [mypy]
    ignore_missing_imports = true

To enforce all your projects to ignore missing imports, add this to your `nitpick-style.toml` file:

    ["setup.cfg".mypy]
    ignore_missing_imports = true

### Absent files

To enforce that certain files should not exist in the project, you can add them to the style file.

    [nitpick.files.absent]
    "some_file.txt" = "This is an optional extra string to display after the warning"
    "another_file.env" = ""

Multiple files can be configured as above.
The message is optional.

## setup.cfg

### Comma separated values

On `setup.cfg`, some keys are lists of multiple values separated by commas, like `flake8.ignore`.

On the style file, it's possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.
Multiple keys can be added.

    [nitpick.files."setup.cfg"]
    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]
