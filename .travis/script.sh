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

if [[ "$ARG_OS_NAME" == 'linux' ]]; then
    echo "Running pytest with coverage report on Linux"
    poetry run coverage run --branch --parallel-mode --source=nitpick -m pytest
else
    echo "Running pytest with coverage report on Windows"
    export PYTEST_DEBUG=1
    poetry run coverage run --branch --parallel-mode --source=nitpick -m pytest
#    poetry run pytest
    # TODO pytest is not completing on Travis, on the Windows build.
    # It gets stuck on this line:
    # early skip of rewriting module: text_unidecode [assertion]

    # It fails after 10 minutes with this message:
    # No output has been received in the last 10m0s, this potentially indicates
    # a stalled build or something wrong with the build itself.
    # Check the details on how to adjust your build configuration on:
    # https://docs.travis-ci.com/user/common-build-problems/#build-times-out-because-no-output-was-received
    # The build has been terminated

    # Those commands also fail:
#    poetry run flake8 --help
#    poetry run flake8
fi
