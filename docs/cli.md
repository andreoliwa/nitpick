# Command-line interface {#cli}

[Nitpick](https://github.com/andreoliwa/nitpick) has a CLI command to fix files automatically.

1.  It doesn't work for all the plugins yet. Currently, it works for:

- [INI plugin](plugins.md#iniplugin) (like `setup.cfg`, `tox.ini`, `.editorconfig`, `.pylintrc`, and any other `.ini`)
- [TOML plugin](plugins.md#tomlplugin)

2.  It tries to preserve the comments and the formatting of the original file.
3.  Some changes still have to be done manually; [Nitpick](https://github.com/andreoliwa/nitpick) cannot guess how to make certain changes automatically.
4.  Run `nitpick fix` to modify files directly, or `nitpick check` to only display the violations.
5.  The [flake8](https://github.com/PyCQA/flake8) plugin only checks the files and doesn't make changes. This is the default for now; once the CLI becomes more stable, the "fix mode" will become the default.
6.  The output format aims to follow [pycodestyle (pep8) default output format](https://github.com/PyCQA/pycodestyle/blob/master/pycodestyle.py#L108).
7.  You can set options through environment variables using the format `NITPICK_command_option`. E.e: `NITPICK_CHECK_VERBOSE=3 nitpick check`. For more details on how this works, see the [Click documentation about CLI options](https://click.palletsprojects.com/en/8.1.x/options/#values-from-environment-variables).

If you use Git, you can review the files before committing.

The available commands are described below.

## Suggest styles based on project files

You can use the `nitpick init --suggest` command to suggest styles based on the files in your project.

Nitpick will scan the files starting from the project root, skipping the ones ignored by Git, and suggest the styles that match the file types.

By default, it will suggest the styles from the built-in library. You can use the `--library` option to scan a custom directory with styles.

The directory structure of your custom library should be the same as the built-in library: `<root_library_dir>/<file_type>/<your_style_name>.toml`.

- `file_type` can be any tag reported by the [pre-commit/identify library](https://github.com/pre-commit/identify) (e.g. `python`, `yaml`, `markdown`, etc.);
- use the special type `any` for styles that apply to all file types (e.g. trim trailing whitespace).

<!-- auto-generated-from-here -->

## Main options {#cli_cmd}

```
Usage: nitpick [OPTIONS] COMMAND [ARGS]...

  Enforce the same settings across multiple language-independent projects.

Options:
  -p, --project DIRECTORY  Path to project root
  --offline                Offline mode: no style will be downloaded (no HTTP
                           requests at all)
  --version                Show the version and exit.
  --help                   Show this message and exit.

Commands:
  check  Don't modify files, just print the differences.
  fix    Fix files, modifying them directly.
  init   Create or update the [tool.nitpick] table in the configuration...
  ls     List of files configured in the Nitpick style.
```

## `fix`: Modify files directly {#cli_cmd_fix}

At the end of execution, this command displays:

- the number of fixed violations;
- the number of violations that have to be changed manually.

```
Usage: nitpick fix [OPTIONS] [FILES]...

  Fix files, modifying them directly.

  You can use partial and multiple file names in the FILES argument.

Options:
  -v, --verbose  Increase logging verbosity (-v = INFO, -vv = DEBUG)
  --help         Show this message and exit.
```

## `check`: Don't modify, just print the differences {#cli_cmd_check}

```
Usage: nitpick check [OPTIONS] [FILES]...

  Don't modify files, just print the differences.

  Return code 0 means nothing would change. Return code 1 means some files
  would be modified. You can use partial and multiple file names in the FILES
  argument.

Options:
  -v, --verbose  Increase logging verbosity (-v = INFO, -vv = DEBUG)
  --help         Show this message and exit.
```

## `ls`: List configures files {#cli_cmd_ls}

```
Usage: nitpick ls [OPTIONS] [FILES]...

  List of files configured in the Nitpick style.

  Display existing files in green and absent files in red. You can use partial
  and multiple file names in the FILES argument.

Options:
  --help  Show this message and exit.
```

## `init`: Initialise a configuration file {#cli_cmd_init}

```
Usage: nitpick init [OPTIONS] [STYLE_URLS]...

  Create or update the [tool.nitpick] table in the configuration file.

Options:
  -f, --fix                Autofix the files changed by the command;
                           otherwise, just print what would be done
  -s, --suggest            Suggest styles based on the extension of project
                           files (skipping Git ignored files)
  -l, --library DIRECTORY  Library dir to scan for style files (implies
                           --suggest); if not provided, uses the built-in
                           style library
  --help                   Show this message and exit.
```
