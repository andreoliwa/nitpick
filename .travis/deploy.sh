#!/usr/bin/env bash
set -exu
echo "Installed versions"
python --version
python3 --version
pyenv --version
pyenv version

echo "Starting deployment"
python3 -m pip install --upgrade pip poetry pre-commit bumpversion twine
npm install -g semantic-release @semantic-release/changelog \
    @semantic-release/git @semantic-release/exec
semantic-release
