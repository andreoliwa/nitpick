#!/usr/bin/env python3
"""Remove pre-commit hooks that don't run on Python 3.5."""
from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()
data = yaml.load(Path(".pre-commit-config.yaml"))
all_repos = data.pop("repos")
# black needs Python >= 3.6
clean_repos = [repo for repo in all_repos if "black" not in repo["repo"]]
data["repos"] = clean_repos

new_config = Path(".travis/.temp-without-black.yaml")
yaml.dump(data, new_config)
print("Saved {}".format(new_config))
