# Create the cache dir if it doesn't exist
$(shell mkdir -p .cache/make)

.PHONY: Makefile

build: always-run .cache/make/long-pre-commit .cache/make/long-poetry .cache/make/lint .cache/make/test .cache/make/doc # Build the project (default target if you simply run `make` without targets)
.PHONY: build

help:
	@echo 'Choose one of the following targets:'
	@cat Makefile | egrep '^[a-z0-9 ./-]*:.*#' | sed -E -e 's/:.+# */@ /g' -e 's/ .+@/@/g' | sort | awk -F@ '{printf "  \033[1;34m%-10s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo 'Run 'make -B' or 'make --always-make' to force a rebuild of all targets'
.PHONY: help

clean: clean-test # Clean all build output (cache, tox, coverage)
	rm -rf .cache .mypy_cache docs/_build src/*.egg-info
.PHONY: clean

clean-test: # Clean test output
	rm -rf .pytest_cache .tox .coverage htmlcov/
.PHONY: clean-test

# Remove cache files if they are older than the configured time, so the targets will be rebuilt
# "fd" is a faster alternative to "find": https://github.com/sharkdp/fd
always-run:
	@fd --changed-before 12h long .cache/make --exec-batch rm -v '{}' ;
	@fd --changed-before 30m short .cache/make --exec-batch rm -v '{}' ;
.PHONY: always-run

pre-commit .cache/make/long-pre-commit: .pre-commit-config.yaml .pre-commit-hooks.yaml # Update and install pre-commit hooks
# TODO: isort 5.0.0 is apparently broken, so we can't autoupdate for now
#	pre-commit autoupdate
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	pre-commit gc
	touch .cache/make/long-pre-commit
.PHONY: pre-commit

poetry .cache/make/long-poetry: pyproject.toml # Update dependencies
	poetry update
	poetry install
	touch .cache/make/long-poetry
.PHONY: poetry

lint .cache/make/lint: .github/*/* .travis/* docs/*.py src/*/* styles/*/* tests/*/* nitpick-style.toml .cache/make/long-poetry # Lint the project (tox running pre-commit, flake8)
	tox -e lint
	touch .cache/make/lint
.PHONY: lint

nitpick: # Run the nitpick pre-commit hook to check local style changes
	pre-commit run --all-files nitpick-local
.PHONY: nitpick

flake8: # Run flake8 to check local style changes
	poetry run flake8 --select=NIP
.PHONY: flake8

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

pytest: # Run pytest on the poetry venv (to quickly run tests locally without waiting for tox)
	poetry run pytest
.PHONY: pytest

doc .cache/make/doc: docs/*/* styles/*/* *.rst *.md # Build documentation only
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
	$(MAKE) force=1 build
.PHONY: ci
