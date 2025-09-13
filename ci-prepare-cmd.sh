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

# https://twine.readthedocs.io/en/latest/#twine-check
twine check dist/*

# The slash at the end is important
# https://github.com/python-poetry/poetry/issues/742#issuecomment-609642943
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config --list

# Hide the password
set +x
poetry publish --repository testpypi --username __token__ --password "$PYPI_TEST_PASSWORD"
