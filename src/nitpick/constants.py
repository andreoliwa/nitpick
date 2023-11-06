"""Constants."""
import jmespath

# keep-sorted start
ANY_BUILTIN_STYLE = "any"
CACHE_DIR_NAME = ".cache"
CONFIG_DUNDER_LIST_KEYS = "__list_keys"
CONFIG_KEY_IGNORE_STYLES = "ignore_styles"
CONFIG_KEY_STYLE = "style"
CONFIG_TOOL_KEY = "tool"
DOT = "."
DOT_NITPICK_TOML = ".nitpick.toml"
EDITOR_CONFIG = ".editorconfig"
FLAKE8_PREFIX = "NIP"
GIT_AT_REFERENCE = "@"
GIT_CORE_EXCLUDES_FILE = "core.excludesfile"
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
PYTHON_PYLINTRC = ".pylintrc"
PYTHON_PYPROJECT_TOML = "pyproject.toml"
PYTHON_REQUIREMENTS_STAR_TXT = "requirements*.txt"
PYTHON_SETUP_CFG = "setup.cfg"
PYTHON_SETUP_PY = "setup.py"
PYTHON_TOX_INI = "tox.ini"
READ_THE_DOCS_URL = "https://nitpick.rtfd.io/en/latest/"
RUST_CARGO_STAR = "Cargo.*"
TOML_EXTENSION = ".toml"
# keep-sorted end

# These depend on some constants above, so they can't be sorted automatically
ROOT_PYTHON_FILES = ("app.py", "wsgi.py", "autoapp.py", PYTHON_MANAGE_PY)
ROOT_FILES = (
    DOT_NITPICK_TOML,
    NITPICK_STYLE_TOML,
    PRE_COMMIT_CONFIG_YAML,
    PYTHON_PYPROJECT_TOML,
    PYTHON_SETUP_PY,
    PYTHON_SETUP_CFG,
    PYTHON_REQUIREMENTS_STAR_TXT,
    PYTHON_PIPFILE_STAR,
    PYTHON_TOX_INI,
    JAVASCRIPT_PACKAGE_JSON,
    RUST_CARGO_STAR,
    GOLANG_MOD,
    GOLANG_SUM,
    *ROOT_PYTHON_FILES,
)
CONFIG_FILES = (DOT_NITPICK_TOML, PYTHON_PYPROJECT_TOML)
CONFIG_RUN_NITPICK_INIT_OR_CONFIGURE_STYLE_MANUALLY = (
    f" Run 'nitpick init' or configure a style manually ({', '.join(CONFIG_FILES)})."
    f" See {READ_THE_DOCS_URL}configuration.html"
)
CONFIG_TOOL_NITPICK_KEY = f"{CONFIG_TOOL_KEY}.{PROJECT_NAME}"
JMEX_TOOL_NITPICK = jmespath.compile(CONFIG_TOOL_NITPICK_KEY)
