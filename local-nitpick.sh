#!/usr/bin/env bash
set -x
export PYTHONPATH=.
python -m nitpick fix
#poetry run nitpick fix
