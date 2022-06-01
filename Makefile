.PHONY: install
install:
	pip install -U pip wheel
	pip install -r requirements.txt -r requirements.dev.txt
	pip install -e .

.PHONY: dist
dist:
	rm *.egg-info -rf; python setup.py bdist_wheel
	rm *.egg-info -rf; python setup.py sdist

.PHONY: test
test:
	pytest --junitxml=test-results/junit.xml --cov-report xml --cov=gamma test/