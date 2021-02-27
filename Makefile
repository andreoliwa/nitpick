.DEFAULT_GOAL := build
.PHONY: Makefile

SRC := $(shell find -f docs src -type f -iname '*.py')
DOCS := docs/*.rst *.rst *.md
STYLES := $(shell find styles -type f)
TESTS := $(shell find tests -type f -iname '*.py')
GITHUB = $(shell find .github -type f)
ANY := $(SRC) $(DOCS) $(STYLES) $(TESTS) $(GITHUB)

# Create the cache dir if it doesn't exist
$(shell mkdir -p .cache/make)

help:
	@echo 'Choose one of the following targets:'
	@cat Makefile | egrep '^[a-z0-9 ./-]*:.*#' | sed -E -e 's/:.+# */@ /g' -e 's/ .+@/@/g' | sort | awk -F@ '{printf "  \033[1;34m%-18s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo 'Run 'make -B' or 'make --always-make' to force a rebuild of all targets'
.PHONY: help

build: .cache/make/pytest .cache/make/nitpick .cache/make/pylint .cache/make/pre-commit # Quick build for local development
.PHONY: build

.cache/make/pytest: $(SRC) $(TESTS)
	invoke test
	touch .cache/make/pytest

.cache/make/nitpick: $(ANY)
	invoke nitpick
	touch .cache/make/nitpick

.cache/make/pylint: $(SRC) $(TESTS)
	invoke pylint
	touch .cache/make/pylint

.cache/make/pre-commit: $(ANY)
	invoke pre-commit
	touch .cache/make/pre-commit

.cache/make/doc: $(DOCS) $(STYLES)
	invoke doc
	touch .cache/make/doc

clean: # Clean build output
	find . -type f -name '*.py[co]' -print -delete
	find . -type d -name '__pycache__' -print -delete
	find . -type d \( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \) -print0 | xargs -0 rm -rvf
	rm -rvf .cache .mypy_cache docs/_build src/*.egg-info .pytest_cache .coverage htmlcov/ .tox/
.PHONY: clean
