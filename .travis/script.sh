#!/usr/bin/env bash
export ARG_OS_NAME=$1
export ARG_PYTHON_VERSION=$2

echo "OS = $ARG_OS_NAME"
echo "Python version = $ARG_PYTHON_VERSION"

if [[ "$ARG_OS_NAME" == 'linux' && "$ARG_PYTHON_VERSION" == '3.7' ]]; then
    echo "Run all pre-commit hooks only on Python 3.7 Linux"
    pre-commit run --all-files

    echo "Running flake8 again for nitpick to check itself"
    poetry install  # This is needed to install nitpick itself, not only the dependencies
    poetry run flake8
fi

echo "Running coverage report"
if [[ "$ARG_OS_NAME" == 'linux' ]]; then
    poetry run coverage run --branch --parallel-mode --source=nitpick -m pytest
else
    poetry run pytest
fi
