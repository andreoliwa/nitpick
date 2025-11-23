# Troubleshooting

## Crash on multi-threading

On macOS, [flake8](https://github.com/PyCQA/flake8) might raise this error when calling `requests.get(url)`:

```shell
objc[93329]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called.
objc[93329]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.
```

To solve this issue, add this environment variable to `.bashrc` (or the initialization file for your favorite shell):

```shell
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

Thanks to [this StackOverflow answer](https://stackoverflow.com/questions/50168647/multiprocessing-causes-python-to-crash-and-gives-an-error-may-have-been-in-progr/52230415#52230415).

## ModuleNotFoundError: No module named 'nitpick.plugins.XXX'

When upgrading to new versions, old plugins might be renamed in [setuptools entry points](https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html).

But they might still be present in the [entry_points.txt plugin metadata](https://setuptools.readthedocs.io/en/latest/deprecated/python_eggs.html#entry-points-txt-entry-point-plugin-metadata) in your virtualenv.

```
$ rg nitpick.plugins.setup ~/Library/Caches/pypoetry/
/Users/john.doe/Library/Caches/pypoetry/virtualenvs/nitpick-UU_pZ5zs-py3.7/lib/python3.7/site-packages/nitpick-0.24.1.dist-info/entry_points.txt
11:setup_cfg=nitpick.plugins.setup_cfg
```

Remove and recreate the virtualenv; this should fix it.

During development, you can run `invoke clean --venv install --dry`. It will display the commands that would be executed; remove `--dry` to actually run them.

[Read this page on how to install Invoke](contributing.md#development).

## Executable `.tox/lint/bin/pylint` not found

You might get this error while running `make` locally.

1.  Run `invoke lint` (or `tox -e lint` directly) to create this [tox](https://github.com/tox-dev/tox) environment.
2.  Run `make` again.

## Missing `rev` key when using the default `pre-commit` styles

If you're using the default `pre-commit` styles, you might get this error:

```shell
An error has occurred: InvalidConfigError:
==> File .pre-commit-config.yaml
==> At Config()
==> At key: repos
==> At Repository(repo='https://github.com/PyCQA/bandit')
=====> Missing required key: rev
Check the log at /Users/your-name/.cache/pre-commit/pre-commit.log
```

This happens because the default styles don't have a `rev` key. Currently, this is not possible because the pre-commit plugin doesn't support it.

To solve this, you can run `pre-commit autoupdate` to update the styles to the latest version, as [recommended in the official docs](https://pre-commit.com/#updating-hooks-automatically).

For more details, [check out this comment on the GitHub issue](https://github.com/andreoliwa/nitpick/issues/472#issuecomment-1079692929).
