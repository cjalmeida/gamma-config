#!/usr/bin/env python

"""The setup script."""

import glob
import os

from setuptools import find_namespace_packages, setup

try:
    import setupext_janitor  # NOQA
except ModuleNotFoundError:
    pass


with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

with open("requirements.txt") as f:
    requirements = [x for x in f.read().splitlines() if x and x[0] not in "-# "]

setup_requirements = ["pytest-runner", "setupext_janitor"]

test_requirements = [
    "pytest>=3",
]

config_sample = [x for x in glob.glob("config/**", recursive=True) if os.path.isfile(x)]
data_files = [("config", config_sample)]

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
    data_files=data_files,
    description="Gamma Config",
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="bcg gamma cli config",
    name="gamma-config",
    packages=find_namespace_packages(exclude=["test", "test.*", "test.gamma.config.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/devex-br/gamma-config",
    version="0.1.1",
    zip_safe=False,
    entry_points={"gamma.cli": ["config-cli = gamma.config.cli"]},
)
