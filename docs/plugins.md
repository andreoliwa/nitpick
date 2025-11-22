# Plugins

Nitpick uses plugins to handle configuration files.

There are plans to add plugins that handle certain file types, specific files, and user plugins. Check [the roadmap](https://github.com/andreoliwa/nitpick/projects/1).

Below are the currently included plugins.

<!-- auto-generated-from-here -->

## INI files {#iniplugin}

Enforce configurations and autofix INI files.

Examples of `.ini` files handled by this plugin:

- [setup.cfg](https://setuptools.pypa.io/en/latest/setuptools.html#setup-cfg-only-projects)
- [.editorconfig](https://editorconfig.org/)
- [tox.ini](https://github.com/tox-dev/tox)
- [.pylintrc](https://pylint.readthedocs.io/en/latest/user_guide/usage/run.html#command-line-options)

Style examples enforcing values on INI files: [flake8 configuration](https://github.com/andreoliwa/nitpick/blob/master/src/nitpick/resources/python/flake8.toml).

## JSON files {#jsonplugin}

Enforce configurations and autofix JSON files.

Add the configurations for the file name you wish to check.
Style example: [the default config for package.json](https://github.com/andreoliwa/nitpick/blob/master/src/nitpick/resources/javascript/package-json.toml).

## Text files {#textplugin}

Enforce configuration on text files.

To check if `some.txt` file contains the lines `abc` and `def` (in any order):

```toml
[["some.txt".contains]]
line = "abc"

[["some.txt".contains]]
line = "def"
```

## TOML files {#tomlplugin}

Enforce configurations and autofix TOML files.

E.g.: [pyproject.toml (PEP 518)](https://www.python.org/dev/peps/pep-0518/#file-format).

See also [the [tool.poetry] section of the pyproject.toml file](https://github.com/python-poetry/poetry/blob/master/docs/pyproject.md).

Style example: [Python 3.10 version constraint](https://github.com/andreoliwa/nitpick/blob/master/src/nitpick/resources/python/310.toml).
There are [many other examples in the library](https://nitpick.rtfd.io/en/latest/library.html).

## YAML files {#yamlplugin}

Enforce configurations and autofix YAML files.

- Example: [.pre-commit-config.yaml](https://pre-commit.com/#pre-commit-configyaml---top-level).
- Style example: [the default pre-commit hooks](https://github.com/andreoliwa/nitpick/blob/master/src/nitpick/resources/any/pre-commit-hooks.toml).

!!! warning

    The plugin tries to preserve comments in the YAML file by using the `ruamel.yaml` package.
    It works for most cases.
    If your comment was removed, place them in a different place of the fil and try again.
    If it still doesn't work, please [report a bug](https://github.com/andreoliwa/nitpick/issues/new/choose).

Known issue: lists like `args` and `additional_dependencies` might be joined in a single line,
and comments between items will be removed.
Move your comments outside these lists, and they should be preserved.

!!! note

    No validation of `.pre-commit-config.yaml` will be done anymore in this generic YAML plugin.
    Nitpick will not validate hooks and missing keys as it did before; it's not the purpose of this package.
