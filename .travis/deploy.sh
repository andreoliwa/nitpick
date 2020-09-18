#!/usr/bin/env bash
set -exu
echo "Installed versions"
python --version
python3 --version
pyenv --version
pyenv version
pyenv versions
pip --version

echo "Starting deployment"
pyenv global 3.7.1
pip3 install --upgrade pip poetry pre-commit bumpversion twine
npm install -g semantic-release @semantic-release/changelog \
    @semantic-release/git @semantic-release/exec
semantic-release
