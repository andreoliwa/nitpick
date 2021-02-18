.DEFAULT_GOAL := quick

# Create the cache dir if it doesn't exist
$(shell mkdir -p .cache/make)

.PHONY: Makefile

help:
	@echo 'Choose one of the following targets:'
	@cat Makefile | egrep '^[a-z0-9 ./-]*:.*#' | sed -E -e 's/:.+# */@ /g' -e 's/ .+@/@/g' | sort | awk -F@ '{printf "  \033[1;34m%-18s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo 'Run 'make -B' or 'make --always-make' to force a rebuild of all targets'
.PHONY: help

build: .remove-old-cache .cache/make/lint .cache/make/test-one .cache/make/doc # Simple build: no upgrades (pre-commit/Poetry), test only latest Python. For local development and bug fixes (default target)
.PHONY: build

quick: pytest nitpick pre-commit pylint # Run pytest and pre-commit fast, without tox
.PHONY: quick

full-build: .remove-old-cache .cache/make/long-pre-commit .cache/make/long-poetry .cache/make/lint .cache/make/test .cache/make/doc # Build the project fully, like in CI
.PHONY: full-build

clean: clean-test # Clean all build output (cache, tox, coverage)
	rm -rf .cache .mypy_cache docs/_build src/*.egg-info
.PHONY: clean

clean-test: # Clean test output
	rm -rf .pytest_cache .tox .coverage htmlcov/
.PHONY: clean-test

# Remove cache files if they are older than the configured time, so the targets will be rebuilt
# "fd" is a faster alternative to "find": https://github.com/sharkdp/fd
.remove-old-cache:
	@fd --changed-before 12h long .cache/make --exec-batch rm -v '{}' ;
	@fd --changed-before 30m short .cache/make --exec-batch rm -v '{}' ;
.PHONY: .remove-old-cache

install: install-pre-commit install-poetry # Install pre-commit hooks and Poetry dependencies
.PHONY: install

# Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy
install-poetry .cache/make/long-poetry src/nitpick.egg-info/entry_points.txt: pyproject.toml # Install Poetry dependencies
	poetry install -E test -E lint
	touch .cache/make/long-poetry
.PHONY: install-poetry

install-pre-commit .cache/make/long-pre-commit: .pre-commit-config.yaml .pre-commit-hooks.yaml # Install pre-commit hooks
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	pre-commit gc
	touch .cache/make/long-pre-commit
.PHONY: install-pre-commit

update: update-pre-commit update-poetry # Update pre-commit hooks and Poetry dependencies
.PHONY: update

update-pre-commit: # Update pre-commit hooks
	@# Uncomment the line below to auto update all repos except a few filtered out with egrep
	yq -r '.repos[].repo' .pre-commit-config.yaml | egrep -v -e '^local' -e commitlint | sed -E -e 's/http/--repo http/g' | xargs pre-commit autoupdate
.PHONY: update-pre-commit

update-poetry: # Update Poetry dependencies
	poetry update
.PHONY: update-poetry

lint .cache/make/lint: .github/*/* .travis/* docs/*.py src/*/* styles/*/* tests/*/* nitpick-style.toml .cache/make/long-poetry # Lint the project (tox running pre-commit, flake8)
	tox -e lint
	touch .cache/make/lint
.PHONY: lint

pre-commit: # Run pre-commit for all files
	pre-commit run --all-files
.PHONY: pre-commit

pylint: # Run pylint for all files
	poetry run pylint src/
.PHONY: pylint

nitpick: # Run Nitpick locally on itself (with flake8)
	poetry run flake8 --select=NIP
.PHONY: nitpick

TOX_PYTHON_ENVS = $(shell tox -l | egrep '^py' | xargs echo | tr ' ' ',')

test .cache/make/test: .cache/make/long-poetry src/*/* styles/*/* tests/*/* # Run tests (use failed=1 to run only failed tests)
ifdef failed
	tox -e ${TOX_PYTHON_ENVS} --failed
else
	@rm -f .pytest/failed
	tox -e "clean,${TOX_PYTHON_ENVS},report"
endif
	touch .cache/make/test
.PHONY: test

test-one .cache/make/test-one: .cache/make/long-poetry src/*/* styles/*/* tests/*/* # Run tests on a single Python version
	tox -e py36
	touch .cache/make/test-one
.PHONY: test

pytest: src/nitpick.egg-info/entry_points.txt # Run pytest on the poetry venv (to quickly run tests locally without waiting for tox)
	poetry run python -m pytest --doctest-modules
.PHONY: pytest

doc .cache/make/doc: docs/*/* styles/*/* *.rst *.md # Build documentation only
	mkdir -p docs/_static
	@rm -rf docs/source
	tox -e docs
	touch .cache/make/doc
.PHONY: doc

tox: # Run full tox (recreating environments)
	tox -r
	touch .cache/make/lint
	touch .cache/make/test
	touch .cache/make/doc
.PHONY: tox

ci: # Simulate CI run (force clean docs and tests, but do not update pre-commit nor Poetry)
	@rm -rf .cache/make/*doc* .cache/make/lint .cache/make/test docs/_build docs/source
	$(MAKE) force=1 full-build
.PHONY: ci
