#!/usr/bin/env bash
pyenv # fixme
pip install -U poetry pre-commit bumpversion twine
npm install -g semantic-release@15 @semantic-release/changelog @semantic-release/git @semantic-release/exec
semantic-release
