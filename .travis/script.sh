#!/usr/bin/env bash
export ARG_OS_NAME=$1
export ARG_PYTHON_VERSION=$2

echo "OS = $ARG_OS_NAME"
echo "Python version = $ARG_PYTHON_VERSION"

if [[ "$ARG_OS_NAME" == 'linux' ]]; then
    tox
    echo "Running pytest with coverage report on Linux"
    poetry run coverage run --branch --parallel-mode --source=src -m pytest  # FIXME: move to tox.ini
else
    # TODO Several commands don't work on the Windows build on Travis.
    echo "Running pytest with coverage report on Windows"

    # Build freezes with message:
    # Spawning shell within C:\Users\travis\AppData\Local\pypoetry\Cache\virtualenvs\nitpick-py3.7
    # poetry shell

    export PYTEST_DEBUG=1
    # Build shows debug messages and freezes on this line:
    # early skip of rewriting module: text_unidecode [assertion]

    # Build fails with message:
    # No module named 'pytest'
    # /c/Users/travis/AppData/Local/pypoetry/Cache/virtualenvs/nitpick-py3.7/activate.bat

    # Build freezes with no message:
    # poetry run flake8 --help
    # poetry run flake8

    coverage run --branch --parallel-mode --source=src -m pytest
    # Build freezes on test collection:
    # ============================= test session starts =============================
    # platform win32 -- Python 3.7.4, pytest-5.2.2, py-1.8.0, pluggy-0.13.0 -- c:\users\travis\appdata\local\pypoetry\cache\virtualenvs\nitpick-py3.7\scripts\python.exe
    # cachedir: .pytest_cache
    # rootdir: C:\Users\travis\build\andreoliwa\nitpick, inifile: setup.cfg
    # plugins: repeat-0.8.0, runfailed-0.6
    # collecting ...

    # All builds fail after 10 minutes with this message:
    # No output has been received in the last 10m0s, this potentially indicates
    # a stalled build or something wrong with the build itself.
    # Check the details on how to adjust your build configuration on:
    # https://docs.travis-ci.com/user/common-build-problems/#build-times-out-because-no-output-was-received
    # The build has been terminated
fi
