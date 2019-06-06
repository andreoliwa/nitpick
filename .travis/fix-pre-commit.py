#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean up the pre-commit configuration and remove black, because it doesn't run on Python 3.5."""
from pathlib import Path

import yaml

config_file = Path(".pre-commit-config.yaml")
data = yaml.safe_load(config_file.open())
all_repos = data.pop("repos")
clean_repos = [repo for repo in all_repos if "black" not in repo["repo"]]
data["repos"] = clean_repos

new_config = Path(".travis/.temp-without-black.yaml").resolve()
yaml.dump(data, new_config.open("w"))
print("Saved {}".format(new_config))
