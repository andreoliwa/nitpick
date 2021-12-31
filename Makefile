.DEFAULT_GOAL := build
.PHONY: Makefile

SRC := $(shell find docs src -type f -a -iname '*.py')
DOCS := docs/*.rst *.rst *.md
STYLES := $(shell find src/nitpick/resources -type f)
TESTS := $(shell find tests -type f -iname '*.py')
GITHUB = $(shell find .github -type f)
ANY := $(SRC) $(DOCS) $(STYLES) $(TESTS) $(GITHUB)

# Create the cache dir if it doesn't exist
$(shell mkdir -p .cache/make)

help:
	@echo "Make targets (run 'make -B' or 'make --always-make' to force):"
	@cat Makefile | egrep '^[a-z0-9 ./-]*:.*#' | sed -E -e 's/:.+# */@ /g' -e 's/ .+@/@/g' | sort | awk -F@ '{printf "  \033[1;34m%-18s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo 'Use invoke to run other tasks that were previously make targets:'
	invoke --list
.PHONY: help

build: .cache/make/pytest .cache/make/pre-commit # Quick build for local development
.PHONY: build

.cache/make/pytest: $(SRC) $(TESTS)
	invoke test
	touch .cache/make/pytest

.cache/make/pre-commit: $(ANY)
	# Force a cache update before running "nitpick fix" in pre-commit
	# TODO: the cache doesn't detect changes in TOML style files
	rm -rf .cache/nitpick
	pre-commit run -a
	touch .cache/make/pre-commit

.cache/make/doc: $(DOCS) $(STYLES)
	invoke doc
	touch .cache/make/doc
