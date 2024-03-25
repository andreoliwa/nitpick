"""Constants."""

from __future__ import annotations

import os
import re
from datetime import timedelta
from enum import Enum, IntEnum, auto

import jmespath
from requests_cache import DO_NOT_CACHE, NEVER_EXPIRE

# keep-sorted start
ANY_BUILTIN_STYLE = "any"
CACHE_DIR_NAME = ".cache"
COMMENT_MARKER_END = "-end"
COMMENT_MARKER_START = "-start"
CONFIG_DUNDER_LIST_KEYS = "__list_keys"
CONFIG_KEY_IGNORE_STYLES = "ignore_styles"
CONFIG_KEY_STYLE = "style"
CONFIG_KEY_TOOL = "tool"
CONFIG_TOOL_KEY = "tool"
DOT = "."
DOT_NITPICK_TOML = ".nitpick.toml"
EDITOR_CONFIG = ".editorconfig"
FLAKE8_PREFIX = "NIP"
GITHUB_COM = "github.com"
GITHUB_COM_API = "api.github.com"
GITHUB_COM_QUERY_STRING_TOKEN = "token"  # nosec # noqa: S105
GITHUB_COM_RAW = "raw.githubusercontent.com"
GIT_AT_REFERENCE = "@"
GIT_CORE_EXCLUDES_FILE = "core.excludesFile"
GIT_DIR = ".git"
GIT_IGNORE = ".gitignore"
GOLANG_MOD = "go.mod"
GOLANG_SUM = "go.sum"
JAVASCRIPT_PACKAGE_JSON = "package.json"
JMEX_NITPICK_MINIMUM_VERSION = jmespath.compile("nitpick.minimum_version")
JMEX_NITPICK_STYLES_INCLUDE = jmespath.compile("nitpick.styles.include")
MERGED_STYLE_TOML = "merged-style.toml"
NITPICK_STYLE_TOML = "nitpick-style.toml"
PRE_COMMIT_CONFIG_YAML = ".pre-commit-config.yaml"
PROJECT_NAME = "nitpick"
PROJECT_OWNER = "andreoliwa"
PYTHON_MANAGE_PY = "manage.py"
PYTHON_PIPFILE_STAR = "Pipfile*"
PYTHON_POETRY_TOML = "poetry.toml"
PYTHON_PYLINTRC = ".pylintrc"
PYTHON_PYPROJECT_TOML = "pyproject.toml"
PYTHON_REQUIREMENTS_STAR_TXT = "requirements*.txt"
PYTHON_SETUP_CFG = "setup.cfg"
PYTHON_SETUP_PY = "setup.py"
PYTHON_TOX_INI = "tox.ini"
READ_THE_DOCS_URL = "https://nitpick.rtfd.io/en/latest/"
REGEX_CACHE_UNIT = re.compile(r"(?P<number>\d+)\s+(?P<unit>(minute|hour|day|week))", re.IGNORECASE)
RUST_CARGO_STAR = "Cargo.*"
TOML_EXTENSION = ".toml"
WRITE_STYLE_MAX_ATTEMPTS = 5
# keep-sorted end

# These depend on some constants above, so they can't be sorted automatically
ROOT_PYTHON_FILES = ("app.py", "wsgi.py", "autoapp.py", PYTHON_MANAGE_PY)
ROOT_FILES = (
    # keep-sorted start
    *ROOT_PYTHON_FILES,
    DOT_NITPICK_TOML,
    GOLANG_MOD,
    GOLANG_SUM,
    JAVASCRIPT_PACKAGE_JSON,
    NITPICK_STYLE_TOML,
    PRE_COMMIT_CONFIG_YAML,
    PYTHON_PIPFILE_STAR,
    PYTHON_POETRY_TOML,
    PYTHON_PYPROJECT_TOML,
    PYTHON_REQUIREMENTS_STAR_TXT,
    PYTHON_SETUP_CFG,
    PYTHON_SETUP_PY,
    PYTHON_TOX_INI,
    RUST_CARGO_STAR,
    # keep-sorted end
)
# Config files in the order they are searched for
CONFIG_FILES = (DOT_NITPICK_TOML, PYTHON_PYPROJECT_TOML)
CONFIG_RUN_NITPICK_INIT_OR_CONFIGURE_STYLE_MANUALLY = (
    f" Run 'nitpick init' or configure a style manually ({', '.join(CONFIG_FILES)})."
    f" See {READ_THE_DOCS_URL}configuration.html"
)
CONFIG_TOOL_NITPICK_KEY = f"{CONFIG_TOOL_KEY}.{PROJECT_NAME}"
JMEX_TOOL_NITPICK = jmespath.compile(CONFIG_TOOL_NITPICK_KEY)


class EmojiEnum(Enum):
    """Emojis used in the CLI."""

    # keep-sorted start
    CONSTRUCTION = "🚧"
    GREEN_CHECK = "✅"
    QUESTION_MARK = "❓"
    SLEEPY_FACE = "😴"
    STAR_CAKE = "✨ 🍰 ✨"
    X_RED_CROSS = "❌"
    # keep-sorted end


class _OptionMixin:
    """Private mixin used to test the CLI options."""

    name: str

    def as_flake8_flag(self) -> str:
        """Format the name of a flag to be used on the CLI."""
        slug = self.name.lower().replace("_", "-")
        return f"--{PROJECT_NAME}-{slug}"

    def as_envvar(self) -> str:
        """Format the name of an environment variable."""
        return f"{PROJECT_NAME.upper()}_{self.name.upper()}"

    def get_environ(self) -> str:
        """Get the value of an environment variable."""
        return os.environ.get(self.as_envvar(), "")


class Flake8OptionEnum(_OptionMixin, Enum):
    """Options to be used with the ``flake8`` plugin/CLI."""

    OFFLINE = "Offline mode: no style will be downloaded (no HTTP requests at all)"


class CachingEnum(IntEnum):
    """Caching modes for styles."""

    #: Never cache, the style file(s) are always looked-up.
    NEVER = auto()

    #: Once the style(s) are cached, they never expire.
    FOREVER = auto()

    #: The cache expires after the configured amount of time (minutes/hours/days).
    EXPIRES = auto()


# TODO: move this to the enum above
CACHE_EXPIRATION_DEFAULTS = {
    CachingEnum.NEVER: DO_NOT_CACHE,
    CachingEnum.FOREVER: NEVER_EXPIRE,
    CachingEnum.EXPIRES: timedelta(hours=1),
}
