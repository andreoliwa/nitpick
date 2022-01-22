"""Meta tests for sanity check purposes."""
import json
from configparser import ConfigParser
from pathlib import Path

from testfixtures import compare

from nitpick.constants import PACKAGE_JSON

REPO_ROOT = Path(__file__).parent.parent


def test_bumpversion_files_match_package_json():
    """Files changed by bumpversion should be present in package.json Git assets.

    So they are committed when a new release is created.
    """
    bumpversion_cfg = ConfigParser()
    bumpversion_cfg.read(REPO_ROOT / ".bumpversion.cfg")
    bumpversion_files = {section.split(":")[2] for section in bumpversion_cfg.sections() if ":file:" in section}

    package_json = Path(REPO_ROOT / PACKAGE_JSON)
    package_json_dict = json.loads(package_json.read_text())
    package_json_git_files = set(
        [
            obj[1]["assets"]
            for obj in package_json_dict["release"]["plugins"]
            if isinstance(obj, list) and "/git" in obj[0]
        ][0]
    )

    package_json_git_files.remove(".bumpversion.cfg")
    package_json_git_files.remove("CHANGELOG.md")
    compare(bumpversion_files, package_json_git_files)
