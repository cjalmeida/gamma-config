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
#   # PyPI Release
	. .env && \
	twine check dist/* && \
	twine upload --verbose -r testpypi -u __token__ -p "$$TEST_PYPY_TOKEN" dist/*

#   # GH Release
	gh release create `git describe` --notes "New release" dist/*


.PHONY: test
test:
	pytest --junitxml=test-results/junit.xml --cov-report xml --cov=gamma test/
