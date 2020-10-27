#!/usr/bin/env python

"""The setup script."""

import os

from setuptools import find_namespace_packages, setup

VERSION=os.getenv("VERSION", "0.1.19")

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("requirements.in") as f:
    requirements = [x for x in f.read().splitlines() if x and x[0] not in "-# "]

setup_requirements = ["pytest-runner"]

test_requirements = [
    "pytest>=3",
]

# collect sample config
data_files = []
for root, _, files in os.walk("config"):
    dst = f"etc/gamma-config/{root}"
    src = [f"{root}/{f}" for f in files]
    data_files.append((dst, src))

print(data_files)

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
    long_description=readme,
    include_package_data=True,
    keywords="bcg gamma cli config",
    name="gamma-config",
    packages=find_namespace_packages(
        include=["gamma.config"], exclude=["test", "test.*", "test.gamma.config.*"]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/devex-br/gamma-config",
    version=VERSION,
    zip_safe=False,
    entry_points={"gamma.cli": ["config-cli = gamma.config.cli_plugin"]},
)
