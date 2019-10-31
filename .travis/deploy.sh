#!/usr/bin/env bash
# Use nvm to install and use the Node LTS version (nvm is installed on all Travis images)
pip install -U poetry pre-commit bumpversion twine
# fixme @semantic-release/changelog @semantic-release/git @semantic-release/exec
npx semantic-release
