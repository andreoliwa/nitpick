# Quickstart

## Install

Install in an isolated global environment with [pipx](https://github.com/pipxproject/pipx):

    # Latest PyPI release
    pipx install nitpick

    # Development branch from GitHub
    pipx install git+https://github.com/andreoliwa/nitpick

On macOS/Linux, install the latest release with [Homebrew](https://github.com/Homebrew/brew):

    brew install andreoliwa/formulae/nitpick

    # Development branch from GitHub
    brew install andreoliwa/formulae/nitpick --HEAD

On Arch Linux, install with yay:

    yay -Syu nitpick

Add to your project with [uv](https://docs.astral.sh/uv/):

    uv add --dev nitpick

Add to your project with [Poetry](https://github.com/python-poetry/poetry):

    poetry add --dev nitpick

Or install it with pip:

    pip install -U nitpick

## Run

Nitpick will fail if no style is explicitly configured. Run this command to download and use the opinionated
[default style file]({{ github_url('nitpick-style.toml') }}):

    nitpick init

You can use it as a template to configure your own style.

To fix and modify your files directly:

    nitpick fix

To check for errors only:

    nitpick check

Nitpick is also a [flake8](https://github.com/PyCQA/flake8) plugin, so
you can run this on a project with at least one Python (`.py`) file:

    flake8 .

## Run as a pre-commit hook

If you use [pre-commit](https://pre-commit.com/) on your project, add
this to the `.pre-commit-config.yaml` in your repository:

There are a few hook IDs available.
The recommendation is to choose `nitpick-suggest` and one of the fix/check hooks.

```yaml
repos:
  - repo: https://github.com/andreoliwa/nitpick
    rev: v0.38.0
    hooks:
      # This hook runs the `nitpick init --fix --suggest` command
      - id: nitpick-suggest

      # Choose only one of the "fix" or "check" hooks.
      # These hooks run the `nitpick fix` command
      - id: nitpick
      # - id: nitpick-fix-all # same as nitpick
      # - id: nitpick-fix
      # These hooks run the `nitpick check` command
      # - id: nitpick-check-all
      # - id: nitpick-check
```

If you want to run Nitpick as a [flake8](https://github.com/PyCQA/flake8) plugin instead:

```yaml
repos:
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        additional_dependencies: [nitpick]
```

To install the `pre-commit` and `commit-msg` Git hooks
using [prek (pre-commit re-engineered in Rust)](https://github.com/j178/prek):

    prek install --install-hooks
    prek install -t commit-msg

To start checking all your code against the default rules:

    prek run --all-files

## Run as a MegaLinter plugin

If you use [MegaLinter](https://megalinter.github.io/) you can run
Nitpick as a plugin. Add the following two entries to your `.mega-linter.yml` configuration file:

```yaml
PLUGINS:
  - https://raw.githubusercontent.com/andreoliwa/nitpick/v0.38.0/mega-linter-plugin-nitpick/nitpick.megalinter-descriptor.yml
ENABLE_LINTERS:
  - NITPICK
```
