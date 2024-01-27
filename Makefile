SHELL=/bin/bash

.PHONY: install
install:
	pdm --version
	pdm install

.PHONY: build
build:
	pdm build

.PHONY: tag-push
tag-push: ACTION=patch
tag-push:
	bumpversion $(ACTION)
	git push origin --all && git push origin --tags
	$(MAKE) deploy


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
	ghp-import -n -p -f site

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
