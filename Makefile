SHELL=/bin/bash

.PHONY: install
install:
	pip install -U pip wheel
	pip install -r requirements.txt -r requirements.dev.txt
	pip install -e .

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
	pytest --junitxml=test-results/junit.xml --cov-report xml --cov=gamma test/
