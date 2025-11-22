# Styles

## The style file

A "Nitpick code style" is a [TOML](https://github.com/toml-lang/toml) file with the settings that should be present in config files from other tools.

Example of a style:

```toml
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

This example style will assert that:

- \... [black](https://github.com/psf/black), [isort](https://github.com/PyCQA/isort) and [flake8](https://github.com/PyCQA/flake8) have a line length of 120;
- \... [flake8](https://github.com/PyCQA/flake8) and [isort](https://github.com/PyCQA/isort) are configured with the above options in `setup.cfg`;
- \... [Pylint](https://github.com/PyCQA/pylint) is present as a [Poetry](https://github.com/python-poetry/poetry) dev dependency in `pyproject.toml`.

## Configure your own style

After creating your own [TOML](https://github.com/toml-lang/toml) file with your style, add it to your `pyproject.toml` file. See [configuration](configuration.md) for details.

You can also check [the style library](library.md), and use the styles to build your own.

## Default search order for a style

1.  A file or URL configured in the `pyproject.toml` file, `[tool.nitpick]` section, `style` key, as described in [configuration](configuration.md).
2.  Any [nitpick-style.toml](https://github.com/andreoliwa/nitpick/blob/master/nitpick-style.toml) file found in the current directory (the one in which [flake8](https://github.com/PyCQA/flake8) runs from) or above.
3.  If no style is found, then the [default style file](https://github.com/andreoliwa/nitpick/blob/master/nitpick-style.toml) from GitHub is used.

## Style file syntax

A style file contains basically the configuration options you want to enforce in all your projects.

They are just the config to the tool, prefixed with the name of the config file.

E.g.: To configure the [black](https://github.com/psf/black) formatter with a line length of 120, you use this in your `pyproject.toml`:

```toml
[tool.black]
line-length = 120
```

To enforce that all your projects use this same line length, add this to your `nitpick-style.toml`{.interpreted-text role="gitref"} file:

```toml
["pyproject.toml".tool.black]
line-length = 120
```

It's the same exact section/key, just prefixed with the config file name (`"pyproject.toml".`)

The same works for `setup.cfg`.

To [configure mypy](https://mypy.readthedocs.io/en/latest/config_file.html#config-file-format) to ignore missing imports in your project, this is needed on `setup.cfg`:

```ini
[mypy]
ignore_missing_imports = true
```

To enforce all your projects to ignore missing imports, add this to your `nitpick-style.toml`{.interpreted-text role="gitref"} file:

```toml
["setup.cfg".mypy]
ignore_missing_imports = true
```

## Special configurations

### Comparing elements on lists

!!! note

    At the moment, this feature only works on the YAML plugin.

On YAML files, a list (called a "sequence" in the YAML spec) can contain different elements:

- Scalar values like int, float and string;
- Dictionaries or objects with key/value pairs (called "mappings" in the YAML spec)
- Other lists (sequences).

The default behaviour for all lists: when applying a style, [Nitpick](https://github.com/andreoliwa/nitpick) searches if the element already exists in the list; if not found, the element is appended to the end of list.

1.  With scalar values, [Nitpick](https://github.com/andreoliwa/nitpick) compares the elements by their exact value. Strings are compared in a case-sensitive manner, and spaces are considered.
2.  Dicts are compared by a "hash" of their key/value pairs.

On lists containing dicts, it is possible to define a custom "list key" used to search for an element, overriding the default compare mechanism above.

If an element is found by its key, the other key/values are compared and [Nitpick](https://github.com/andreoliwa/nitpick) applies the difference. If the key doesn't exist, the new dict is appended to the end of the list.

Some files have a predefined configuration:

1.  On `.pre-commit-config.yaml`, repos are searched by their hook IDs.
2.  On GitHub Workflow YAML files, steps are searched by their names.

You can define your own list keys for your YAML files (or override the predefined configs above) by using `__list_keys` on your style:

```toml
["path/from/root/to/your/config.yaml".__list_keys]
"<list expression>" = "<search key expression>"
```

`<list expression>`:

- a dotted path to a list, e.g. `repos`, `path.to.some.key`; or
- a pattern containing wildcards (`?` and `*`). For example, `jobs.*.steps`: all `jobs` containing `steps` will use the same `<search key expression>`.

`<search key expression>`:

- a key from the dict inside the list, e.g. `name`; or
- a parent key and its child key separated by a dot, e.g. `hooks.id`.

!!! warning

    For now, only two-level nesting is possible: parent and child keys.

If you have suggestions for predefined list keys for other popular YAML files not covered by [Nitpick](https://github.com/andreoliwa/nitpick) (e.g.: GitLab CI config), feel free to `create an issue <new/choose>`{.interpreted-text role="issue"} or submit a pull request.

## Breaking changes

!!! warning

    Below are the breaking changes in the style before the API is stable. If your style was working in a previous version and now it's not, check below.

### `missing_message` key was removed

`missing_message` was removed. Use `[nitpick.files.present]` now.

Before:

```toml
[nitpick.files."pyproject.toml"]
missing_message = "Install poetry and run 'poetry init' to create it"
```

Now:

```toml
[nitpick.files.present]
"pyproject.toml" = "Install poetry and run 'poetry init' to create it"
```
