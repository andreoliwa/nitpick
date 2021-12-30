#!/usr/bin/env bash
set -x
export PYTHONPATH=.;src/
ls -ll
which python
python -m nitpick fix
#poetry run nitpick fix
