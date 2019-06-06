#!/usr/bin/env bash
echo "Python version = $TRAVIS_PYTHON_VERSION"

fix=
test "$TRAVIS_PYTHON_VERSION" == '3.4' && fix=fix
test "$TRAVIS_PYTHON_VERSION" == '3.5' && fix=fix

# Run all pre-commit hooks on Travis.
if [[ "$fix" == 'fix' ]]; then
    python3 .travis/fix-pre-commit.py
    pre-commit run --all-files --config .travis/.temp-without-black.yaml
else
    pre-commit run --all-files
fi

echo "Running coverage report"
coverage run --parallel-mode --source=flake8_nitpick -m pytest
