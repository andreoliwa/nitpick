#!/usr/bin/env bash
pyenv activate 3.7
pip3 install -U poetry pre-commit bumpversion twine
npx -p @semantic-release/changelog -p @semantic-release/git -p @semantic-release/exec semantic-release
