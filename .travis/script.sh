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
    export PYTEST_DEBUG=1
    poetry run pytest
    # TODO Windows build is failing on Travis. It gets stuck on pytest,
    # and it fails after 10 minutes with this message:
    # No output has been received in the last 10m0s, this potentially indicates
    # a stalled build or something wrong with the build itself.
    # Check the details on how to adjust your build configuration on:
    # https://docs.travis-ci.com/user/common-build-problems/#build-times-out-because-no-output-was-received
    # The build has been terminated
fi
