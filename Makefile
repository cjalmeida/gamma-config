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
#   # GH Release
	gh release create `git describe` --notes "New release" dist/*

#   # PyPI Release
	. .env && \
	twine check dist/* && \
	twine upload --verbose -u __token__ -p "$$PYPY_TOKEN" dist/*

.PHONY: test
test:
	pytest --junitxml=test-results/junit.xml --cov-report xml --cov=gamma tests/

.PHONY: lint
lint:
	flake8 gamma tests

.PHONY: docs
docs:
	pipx run pydoc-markdown==4.5.1 -p gamma.config -p gamma.dispatch > docs/api.md
