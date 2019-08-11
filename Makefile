# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = docs/_build
RERUN_AFTER   = 4h

.PHONY: help Makefile always-run pre-commit poetry sphinx pytest

dev: always-run .cache/make/auto-pre-commit .cache/make/auto-poetry .cache/make/sphinx .cache/make/run .cache/make/pytest

always-run:
	@mkdir -p .cache/make
	@# Remove files named auto* if they are older than a few hours, so the targets will be rebuilt
	@fd --changed-before $(RERUN_AFTER) auto .cache/make --exec-batch rm '{}' ;

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo 'Extra commands:'
	@echo '  pre-commit  to install and update pre-commit hooks'
	@echo '  poetry      to update dependencies'
	@echo '  sphinx      to build docs'
	@echo '  pytest      to run tests'

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
	touch .cache/make/auto-poetry
	-rm .cache/make/run

sphinx:
	-rm .cache/make/sphinx
	$(MAKE)

# $(O) is meant as a shortcut for $(SPHINXOPTS).
.cache/make/sphinx: docs *.rst *.md
	-rm -rf docs/source
	sphinx-apidoc --force --module-first --separate --implicit-namespaces --output-dir docs/source src/
	@$(SPHINXBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	touch .cache/make/sphinx

.cache/make/run: .github/* .travis/* docs/* src/* styles/* tests/* nitpick-style.toml
	pre-commit run --all-files
	flake8
	touch .cache/make/run

pytest:
	-rm .cache/make/pytest
	$(MAKE)

.cache/make/pytest: src/* styles/* tests/*
	pytest
	touch .cache/make/pytest
