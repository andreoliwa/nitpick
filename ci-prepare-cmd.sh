#!/usr/bin/env bash
set -x
set -e

VERSION=$1
bumpversion --allow-dirty --no-commit --no-tag --new-version "$VERSION" patch

# Clean up the files touched by bumpversion
set +e  # Allow failure; if files are modified, prek returns an exit code > 0
# We need to run using the root config otherwise prek will read test fixtures and think this is a monorepo
prek run --all-files --config .pre-commit-config.yaml end-of-file-fixer trailing-whitespace prettier
set -e

rm -rf dist/
uv build

# https://twine.readthedocs.io/en/latest/#twine-check
twine check dist/*

# Hide the password
set +x
uv publish --repository testpypi --username __token__ --password "$PYPI_TEST_PASSWORD"
