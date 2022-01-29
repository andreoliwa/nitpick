#!/usr/bin/env bash
set -x
set -e

VERSION=$1
bumpversion --allow-dirty --no-commit --no-tag --new-version "$VERSION" patch

# Clean up the files touched by bumpversion
set +e  # Allow failure; if files are modified, pre-commit returns an exit code > 0
pre-commit run --all-files end-of-file-fixer
pre-commit run --all-files trailing-whitespace
pre-commit run --all-files prettier
set -e

rm -rf dist/
poetry build

# Hide the password
set +x
# TODO: ci: use poetry publish instead of twine
twine upload --verbose --disable-progress-bar --skip-existing --password "$TWINE_TEST_PASSWORD" -r testpypi dist/*
