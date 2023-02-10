SHELL=/bin/bash


.PHONY: publish
publish:

	@$(MAKE) build

#   # GH Release
	gh release create `git describe` --notes "New release" dist/*

#   # PyPI Release
	. .env && \
	twine check dist/* && \
	twine upload --verbose -u __token__ -p "$$TEST_PYPY_TOKEN" dist/*

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
