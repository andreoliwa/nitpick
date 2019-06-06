#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove pre-commit hooks that don't run on older Python versions (3.4 and 3.5 on Travis CI)."""
from pathlib import Path

import yaml

config_file = Path(".pre-commit-config.yaml")
data = yaml.safe_load(config_file.open())
all_repos = data.pop("repos")
# TODO remove flake8 from here once nitpick has a PyPI version supporting 3.4 and 3.5
clean_repos = [repo for repo in all_repos if "black" not in repo["repo"] and repo["hooks"][0]["id"] != "flake8"]
data["repos"] = clean_repos

new_config = Path(".travis/.temp-without-black.yaml")
yaml.dump(data, new_config.open("w"))
print("Saved {}".format(new_config))
