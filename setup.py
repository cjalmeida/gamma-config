#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

with open("requirements.txt") as f:
    requirements = [x for x in f.read().splitlines() if x[0] not in "-# "]

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest>=3",
]

setup(
    # There are standard setuptools entries
    author="Cloves Almeida",
    author_email="almeida.cloves@bcg.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Gamma Config",
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="bcg gamma cli config",
    name="gamma-config",
    packages=find_packages(include=["gamma", "gamma.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/devex-br/gamma-config",
    version="0.1.0",
    zip_safe=False,
    # This is where you specify your plugins. It must be under the "gamma.plugins"
    # group.
    entry_points={"gamma.plugins": ["config = gamma.config.plugin"]},
)
