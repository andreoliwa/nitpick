#!/usr/bin/env bash
set -x
set -e
VERSION=$1
bumpversion --allow-dirty --no-commit --no-tag --new-version $VERSION patch
cat pyproject.toml
cat /home/runner/work/nitpick/nitpick/pyproject.toml
pre-commit run --all-files end-of-file-fixer
pre-commit run --all-files trailing-whitespace
rm -rf dist/
poetry build
twine upload --verbose --disable-progress-bar --skip-existing --password $TWINE_TEST_PASSWORD -r testpypi dist/*
