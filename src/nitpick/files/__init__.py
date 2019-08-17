"""Files that are checked by Nitpick."""
# isort:skip_file
# TODO: load all modules under files/*, so get_subclasses() detects them; or use a plugin system?
import nitpick.files.pre_commit  # noqa: F401
import nitpick.files.json  # noqa: F401
