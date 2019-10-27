#!/usr/bin/env bash
echo "Python version = $TRAVIS_PYTHON_VERSION"

fix=
test "$TRAVIS_PYTHON_VERSION" == '3.4' && fix=fix
test "$TRAVIS_PYTHON_VERSION" == '3.5' && fix=fix

# Run all pre-commit hooks on Travis.
if [[ "$fix" == 'fix' ]]; then
    python3 .travis/fix_pre_commit.py
    pre-commit run --all-files --config .travis/.temp-without-black.yaml
else
    pre-commit run --all-files
fi

echo "Running flake8 again for nitpick to check itself"
poetry install  # This is needed to install nitpick itself, not only the dependencies
poetry run flake8

echo "Running coverage report"
poetry run coverage run --branch --parallel-mode --source=nitpick -m pytest
