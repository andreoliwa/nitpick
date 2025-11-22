# Quickstart

## Install

Install in an isolated environment with [pipx](https://github.com/pipxproject/pipx):

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

Add to your project with [Poetry](https://github.com/python-poetry/poetry):

    poetry add --dev nitpick

Or install it with pip:

    pip install -U nitpick

## Run

[Nitpick](https://github.com/andreoliwa/nitpick) will fail if no style is explicitly configured. Run this command to download and use the opinionated [default style file](https://github.com/andreoliwa/nitpick/blob/master/nitpick-style.toml):

```bash
nitpick init
```

You can use it as a template to configure your own style.

To fix and modify your files directly:

    nitpick fix

To check for errors only:

    nitpick check

Nitpick is also a [flake8](https://github.com/PyCQA/flake8) plugin, so you can run this on a project with at least one Python (`.py`) file:

    flake8 .

## Run as a pre-commit hook

If you use [pre-commit](https://pre-commit.com/) on your project, add this to the `.pre-commit-config.yaml` in your repository:

```yaml
repos:
  - repo: https://github.com/andreoliwa/nitpick
    rev: v0.38.0
    hooks:
      - id: nitpick-suggest
      - id: nitpick
```

There are a few hook IDs available:

- `nitpick`, `nitpick-fix` and `nitpick-fix-all` run the `nitpick fix` command;
- `nitpick-check` and `nitpick-check-all` runs `nitpick check`;
- `nitpick-suggest` runs `nitpick init --fix --suggest`;

If you want to run [Nitpick](https://github.com/andreoliwa/nitpick) as a [flake8](https://github.com/PyCQA/flake8) plugin instead:

```yaml
repos:
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        additional_dependencies: [nitpick]
```

To install the `pre-commit` and `commit-msg` Git hooks:

```shell
prek install --install-hooks
prek install -t commit-msg
```

To start checking all your code against the default rules:

```shell
prek run --all-files
```

## Run as a MegaLinter plugin

If you use [MegaLinter](https://megalinter.github.io/) you can run Nitpick as a plugin. Add the following two entries to your `.mega-linter.yml` configuration file:

```yaml
PLUGINS:
  - https://raw.githubusercontent.com/andreoliwa/nitpick/v0.38.0/mega-linter-plugin-nitpick/nitpick.megalinter-descriptor.yml
ENABLE_LINTERS:
  - NITPICK
```

## Modify files directly

[Nitpick](https://github.com/andreoliwa/nitpick) includes a CLI to apply your style and modify the configuration files directly:

```shell
nitpick fix
```

Read more details here: [cli](cli.md).
