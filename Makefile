# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build
RERUN_AFTER   = 4h

.PHONY: help Makefile always-run pre-commit poetry doc test force force-docs

dev: always-run .cache/make/auto-pre-commit .cache/make/auto-poetry .cache/make/doc .cache/make/run .cache/make/test

always-run:
	@mkdir -p .cache/make
	@# Remove files named auto* if they are older than a few hours, so the targets will be rebuilt
	@fd --changed-before $(RERUN_AFTER) auto .cache/make --exec-batch rm '{}' ;

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo 'Extra commands:'
	@echo '  pre-commit  to install and update pre-commit hooks'
	@echo '  poetry      to update dependencies'
	@echo '  doc         to build documentation'
	@echo '  test        to run tests'
	@echo '  force       to force rebuild of all targets in this Makefile'
	@echo '  force-docs  to force rebuild of documentation'

pre-commit:
	-rm .cache/make/auto-pre-commit
	$(MAKE)

.cache/make/auto-pre-commit: .pre-commit-config.yaml .pre-commit-hooks.yaml
	pre-commit autoupdate
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg
	pre-commit gc
	touch .cache/make/auto-pre-commit
	-rm .cache/make/run

poetry:
	-rm .cache/make/auto-poetry
	$(MAKE)

.cache/make/auto-poetry: pyproject.toml
	poetry update
	poetry install

	@# Force creation of a setup.py to avoid this error on "pip install -e nitpick"
	@# ERROR: File "setup.py" not found. Directory cannot be installed in editable mode: ~/Code/nitpick
	@# (A "pyproject.toml" file was found, but editable mode currently requires a setup.py based build.)
	@# Remove this if ever pip changes this behaviour
	poetryx setup-py

	touch .cache/make/auto-poetry
	-rm .cache/make/run

doc: docs/* *.rst *.md
	-rm .cache/make/doc
	$(MAKE)

.cache/make/doc-source: src/*
	-rm -rf docs/source
	sphinx-apidoc --force --module-first --separate --implicit-namespaces --output-dir docs/source src/nitpick/
	touch .cache/make/doc-source

# $(O) is meant as a shortcut for $(SPHINXOPTS).
.cache/make/doc: docs/* *.rst *.md .cache/make/doc-source
	@$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

	@# Detect broken links on the documentation
	@$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O) -blinkcheck

	touch .cache/make/doc

.cache/make/run: .github/* .travis/* docs/**.py src/* docs/_static/styles/* tests/* nitpick-style.toml
	pre-commit run --all-files
	flake8
	touch .cache/make/run

test:
	-rm .cache/make/test
	$(MAKE)

.cache/make/test: src/* docs/_static/styles/* tests/*
	pytest
	touch .cache/make/test

force:
	rm -rf .cache/make docs/_build docs/source
	$(MAKE)

force-docs:
	rm -rf .cache/make/doc* docs/_build docs/source
	$(MAKE)
