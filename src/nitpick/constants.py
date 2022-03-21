"""Constants."""
import jmespath

PROJECT_OWNER = "andreoliwa"
PROJECT_NAME = "nitpick"
FLAKE8_PREFIX = "NIP"
CACHE_DIR_NAME = ".cache"
TOML_EXTENSION = ".toml"
DOT_NITPICK_TOML = f".nitpick{TOML_EXTENSION}"
NITPICK_STYLE_TOML = f"nitpick-style{TOML_EXTENSION}"
MERGED_STYLE_TOML = f"merged-style{TOML_EXTENSION}"
READ_THE_DOCS_URL = "https://nitpick.rtfd.io/en/latest/"

# Special files
# Python
PYPROJECT_TOML = "pyproject.toml"
SETUP_PY = "setup.py"
SETUP_CFG = "setup.cfg"
REQUIREMENTS_STAR_TXT = "requirements*.txt"
PIPFILE_STAR = "Pipfile*"
MANAGE_PY = "manage.py"
ROOT_PYTHON_FILES = ("app.py", "wsgi.py", "autoapp.py", MANAGE_PY)
TOX_INI = "tox.ini"
PYLINTRC = ".pylintrc"
# Tools
PRE_COMMIT_CONFIG_YAML = ".pre-commit-config.yaml"
EDITOR_CONFIG = ".editorconfig"
# JavaScript
PACKAGE_JSON = "package.json"
# Rust
CARGO_STAR = "Cargo.*"
# Golang
GO_MOD = "go.mod"
GO_SUM = "go.sum"
# All root files
ROOT_FILES = (
    DOT_NITPICK_TOML,
    NITPICK_STYLE_TOML,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
    SETUP_PY,
    SETUP_CFG,
    REQUIREMENTS_STAR_TXT,
    PIPFILE_STAR,
    TOX_INI,
    PACKAGE_JSON,
    CARGO_STAR,
    GO_MOD,
    GO_SUM,
) + ROOT_PYTHON_FILES
CONFIG_FILES = (DOT_NITPICK_TOML, PYPROJECT_TOML)

# Config sections and keys
TOOL_KEY = "tool"
TOOL_NITPICK_KEY = f"{TOOL_KEY}.{PROJECT_NAME}"

# JMESPath expressions
TOOL_NITPICK_JMEX = jmespath.compile(TOOL_NITPICK_KEY)
NITPICK_STYLES_INCLUDE_JMEX = jmespath.compile("nitpick.styles.include")
NITPICK_MINIMUM_VERSION_JMEX = jmespath.compile("nitpick.minimum_version")

DOT = "."

GIT_AT_REFERENCE = "@"

# Special configurations for plugins
DUNDER_LIST_KEYS = "__list_keys"
