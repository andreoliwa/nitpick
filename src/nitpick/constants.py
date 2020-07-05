"""Constants."""
import jmespath

PROJECT_NAME = "nitpick"
ERROR_PREFIX = "NIP"
CACHE_DIR_NAME = ".cache"
TOML_EXTENSION = ".toml"
NITPICK_STYLE_TOML = "nitpick-style{}".format(TOML_EXTENSION)
MERGED_STYLE_TOML = "merged-style{}".format(TOML_EXTENSION)
RAW_GITHUB_CONTENT_BASE_URL = "https://raw.githubusercontent.com/andreoliwa/{}".format(PROJECT_NAME)
READ_THE_DOCS_URL = "https://nitpick.rtfd.io/en/latest/"
MANAGE_PY = "manage.py"
ROOT_PYTHON_FILES = ("setup.py", "app.py", "wsgi.py", "autoapp.py")
ROOT_FILES = ("requirements*.txt", "Pipfile") + ROOT_PYTHON_FILES

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'

#: Special unique separator for :py:meth:`flatten()` and :py:meth:`unflatten()`,
# to avoid collision with existing key values (e.g. the default dot separator "." can be part of a pyproject.toml key).
SEPARATOR_FLATTEN = "$#@"

#: Special unique separator for :py:meth:`nitpick.generic.quoted_split()`.
SEPARATOR_QUOTED_SPLIT = "#$@"

# Config sections and keys
TOOL_NITPICK = "tool.nitpick"

# JMESPath expressions
TOOL_NITPICK_JMEX = jmespath.compile(TOOL_NITPICK)
NITPICK_STYLES_INCLUDE_JMEX = jmespath.compile("nitpick.styles.include")
NITPICK_MINIMUM_VERSION_JMEX = jmespath.compile("nitpick.minimum_version")
