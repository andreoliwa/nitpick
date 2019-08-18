# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build
LONG_RERUN    = 4h
SHORT_RERUN   = 30m

.PHONY: help Makefile always-run pre-commit poetry doc test test-failed force force-doc

dev: always-run .cache/make/long-pre-commit .cache/make/long-poetry .cache/make/doc .cache/make/run .cache/make/test

always-run:
	@mkdir -p .cache/make

# Remove cache files if they are older than the configured time, so the targets will be rebuilt
# "fd" is a faster alternative to "find": https://github.com/sharkdp/fd
	@fd --changed-before $(LONG_RERUN) long .cache/make --exec-batch rm '{}' ;
		@fd --changed-before $(SHORT_RERUN) short .cache/make --exec-batch rm '{}' ;

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo 'Extra commands:'
	@echo '  pre-commit  to install and update pre-commit hooks'
	@echo '  poetry      to update dependencies'
	@echo '  doc         to build documentation'
	@echo '  test        to run tests'
	@echo '  force       to force rebuild of all targets in this Makefile'
	@echo '  force-doc   to force rebuild of documentation'

pre-commit:
	-rm .cache/make/long-pre-commit
	$(MAKE)

.cache/make/long-pre-commit: .pre-commit-config.yaml .pre-commit-hooks.yaml
	pre-commit autoupdate
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	pre-commit gc
	touch .cache/make/long-pre-commit
	-rm .cache/make/run

poetry:
	-rm .cache/make/long-poetry
	$(MAKE)

.cache/make/long-poetry: pyproject.toml
	poetry update
	poetry install

# Update the requirements for Read the Docs
# "rg" is a faster alternative to "grep": https://github.com/BurntSushi/ripgrep
	pip freeze | rg -i -e sphinx -e pygments | sort -u > docs/requirements.txt

# Force creation of a setup.py to avoid this error on "pip install -e nitpick"
# ERROR: File "setup.py" not found. Directory cannot be installed in editable mode: ~/Code/nitpick
# (A "pyproject.toml" file was found, but editable mode currently requires a setup.py based build.)
# Remove this if ever pip changes this behaviour
# Install PoetryX from here: https://github.com/andreoliwa/python-clib#poetryx
	poetryx setup-py

	touch .cache/make/long-poetry
	-rm .cache/make/run

doc: docs/* *.rst *.md
	-rm .cache/make/*doc*
	$(MAKE)

.cache/make/short-doc-source:
	-rm -rf docs/source
	sphinx-apidoc --force --module-first --separate --implicit-namespaces --output-dir docs/source src/nitpick/
	touch .cache/make/short-doc-source

.cache/make/doc-defaults: docs/generate_defaults.py styles/*
	python3 docs/generate_defaults.py
	touch .cache/make/doc-defaults

# $(O) is meant as a shortcut for $(SPHINXOPTS).
.cache/make/doc: docs/* *.rst *.md .cache/make/short-doc-source .cache/make/doc-defaults
	@$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Detect broken links on the documentation
# Uses this helper script to avoid slow reruns: https://github.com/andreoliwa/dotfiles/blob/master/bin/rerun_after_time.sh
	@rerun_after_time.sh $(SHORT_RERUN) .cache/make/short-doc-link-check $(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) -blinkcheck
	touch .cache/make/short-doc-link-check

	touch .cache/make/doc

.cache/make/run: .github/* .travis/* docs/**.py src/* styles/* tests/* nitpick-style.toml
	pre-commit run --all-files
	flake8
	touch .cache/make/run

test:
	-rm .cache/make/test
	$(MAKE) .cache/make/test

.cache/make/test: src/* styles/* tests/*
	-rm .pytest/failed
	pytest
	touch .cache/make/test

test-failed:
	pytest --failed
	touch .cache/make/test

force:
	rm -rf .cache/make docs/_build docs/source
	$(MAKE)

force-doc:
	rm -rf .cache/make/*doc* docs/_build docs/source
	$(MAKE)
