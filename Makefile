SHELL=/bin/bash

.PHONY: install
install:
	pdm --version
	pdm install

.PHONY: build
build:
	pdm build

.PHONY: tag-push
tag-push:
	@VERSION=v$$(python -c 'from gamma.config import __version__; print(__version__)') && \
	git tag -a $$VERSION -m "Bump to version $$VERSION" && \
	git push --follow-tags


.PHONY: publish
publish:

	@$(MAKE) build

#   # GH Release
	gh release create `git describe` --notes "New release" dist/*

#   # PyPI Release
	. .env && \
	twine check dist/* && \
	twine upload --verbose -u __token__ -p "$$PYPY_TOKEN" dist/*

#	# Docs
	@$(MAKE) publish-docs

.PHONY: publish-docs
publish-docs:
	@$(MAKE) docs
	npx gh-pages@2.0.1 -d site -t

.PHONY: test
test:
	pytest
	python scripts/update-coverage.py

.PHONY: lint
lint:
	flake8 gamma tests

.PHONY: docs
docs:
	python -m mkdocs build
