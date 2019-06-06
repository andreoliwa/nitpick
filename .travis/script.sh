#!/usr/bin/env bash

# Run all pre-commit hooks on Travis.
if [[ $TRAVIS_PYTHON_VERSION == '3.5' ]]; then
    python3 .travis/fix-pre-commit.py
    pre-commit run --all-files --config .travis/.temp-without-black.yaml
else
    pre-commit run --all-files
fi

coverage run --source=flake8_nitpick -m pytest
