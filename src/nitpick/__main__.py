"""Entrypoint module, in case you use ``python -mnitpick``.

Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""
# pragma: no cover
from nitpick.cli import nitpick_cli
from nitpick.constants import PROJECT_NAME


def main() -> None:
    """Entry point for the application script."""
    nitpick_cli(auto_envvar_prefix=PROJECT_NAME)


if __name__ == "__main__":
    main()
