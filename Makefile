SHELL=/bin/bash

.PHONY: install
install:
	pip install -U pip wheel
	pip install -r requirements.txt -r requirements.dev.txt
	pip install -e .

.PHONY: compile-deps
compile-deps:
	pip-compile requirements.in -q
	pip-compile requirements.dev.in -q

.PHONY: build
build:
	rm dist gamma_config.egg-info -rf
	python -m build


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

.PHONY: lint
lint:
	flake8 gamma tests

.PHONY: docs
docs:
	mkdocs build
	which pipx || (python -m pip install pipx)
	python -m pipx run pydoc-markdown==4.5.1 -p gamma.config -p gamma.dispatch > docs/api.md
