"""Entrypoint module, in case you use ``python -mnitpick``.

Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""

from nitpick.cli import nitpick_cli  # pragma: no cover
from nitpick.constants import PROJECT_NAME  # pragma: no cover


def main() -> None:  # pragma: no cover
    """Entry point for the application script."""
    nitpick_cli(auto_envvar_prefix=PROJECT_NAME)


if __name__ == "__main__":  # pragma: no cover
    main()
