#!/usr/bin/env bash
pyenv local 3.7
pip install --upgrade pip poetry pre-commit bumpversion twine
npm install -g semantic-release@15 @semantic-release/changelog \
    @semantic-release/git @semantic-release/exec
semantic-release
