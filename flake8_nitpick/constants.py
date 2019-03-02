"""Constants."""
NAME = "flake8-nitpick"
ERROR_PREFIX = "NIP"
NITPICK_STYLE_TOML = "nitpick-style.toml"
DEFAULT_NITPICK_STYLE_URL = f"https://raw.githubusercontent.com/andreoliwa/flake8-nitpick/master/{NITPICK_STYLE_TOML}"
ROOT_PYTHON_FILES = ("setup.py", "manage.py", "autoapp.py")
ROOT_FILES = ("requirements*.txt", "Pipfile") + ROOT_PYTHON_FILES
