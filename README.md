# flake8-nitpick

[![PyPI](https://img.shields.io/pypi/v/flake8-nitpick.svg)](https://pypi.python.org/pypi/flake8-nitpick)
[![Travis CI](https://travis-ci.com/andreoliwa/flake8-nitpick.svg?branch=master)](https://travis-ci.com/andreoliwa/flake8-nitpick)
[![Documentation Status](https://readthedocs.org/projects/flake8-nitpick/badge/?version=latest)](https://flake8-nitpick.readthedocs.io/en/latest/?badge=latest)
[![Coveralls](https://coveralls.io/repos/github/andreoliwa/flake8-nitpick/badge.svg?branch=master)](https://coveralls.io/github/andreoliwa/flake8-nitpick?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/901b4b62293cf7f2c4bc/maintainability)](https://codeclimate.com/github/andreoliwa/flake8-nitpick/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/901b4b62293cf7f2c4bc/test_coverage)](https://codeclimate.com/github/andreoliwa/flake8-nitpick/test_coverage)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/flake8-nitpick.svg)](https://pypi.org/project/flake8-nitpick/)
[![Project License](https://img.shields.io/pypi/l/flake8-nitpick.svg)](https://pypi.org/project/flake8-nitpick/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=andreoliwa/flake8-nitpick)](https://dependabot.com)
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

Simply install the package (in a virtualenv or globally, wherever) and run `flake8`:

    $ pip install -U flake8-nitpick
    $ flake8

You will see warnings if your project configuration is different than [the default style file](https://raw.githubusercontent.com/andreoliwa/flake8-nitpick//0.12.0/nitpick-style.toml/nitpick-style.toml).

## Style file

### Configure your own style file

Change your project config on `pyproject.toml`, and configure your own style like this:

    [tool.nitpick]
    style = "https://raw.githubusercontent.com/andreoliwa/flake8-nitpick//0.12.0/nitpick-style.toml/nitpick-style.toml"

You can set `style` with any local file or URL. E.g.: you can use the raw URL of a [GitHub Gist](https://gist.github.com).

You can also use multiple styles and mix local files and URLs:

    [tool.nitpick]
    style = ["/path/to/first.toml", "/another/path/to/second.toml", "https://example.com/on/the/web/third.toml"]

The order is important: each style will override any keys that might be set by the previous .toml file.
If a key is defined in more than one file, the value from the last file will prevail.

### Default search order for a style file

1. A file or URL configured in the `pyproject.toml` file, `[tool.nitpick]` section, `style` key, as [described above](#configure-your-own-style-file).

2. Any `nitpick-style.toml` file found in the current directory (the one in which `flake8` runs from) or above.

3. If no style is found, then [the default style file from GitHub](https://raw.githubusercontent.com/andreoliwa/flake8-nitpick//0.12.0/nitpick-style.toml/nitpick-style.toml) is used.

### Style file syntax

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To [configure the black formatter](https://github.com/ambv/black#configuration-format) with a line length of 120, you use this in your `pyproject.toml`:

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

    [[files.absent]]
    file = "myfile1.txt"

    [[files.absent]]
    file = "another_file.env"
    message = "This is an optional extra string to display after the warning"

Multiple files can be configured as above.
The `message` is optional.

## setup.cfg

### Comma separated values

On `setup.cfg`, some keys are lists of multiple values separated by commas, like `flake8.ignore`.

On the style file, it's possible to indicate which key/value pairs should be treated as multiple values instead of an exact string.
Multiple keys can be added.

    ["setup.cfg".nitpick]
    comma_separated_values = ["flake8.ignore", "isort.some_key", "another_section.another_key"]
