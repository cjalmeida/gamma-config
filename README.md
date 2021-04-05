# Gamma Config

![python](https://img.shields.io/badge/python-3.7%2B-blue)
[![CircleCI](https://cci.gamma.bcg.com/gh/BCG/gamma-config/tree/master.svg?style=shield&circle-token=8106c47ad7a019907079adc538ec98b9ba6b0e95)](https://cci.gamma.bcg.com/gh/BCG/gamma-config/tree/master "master") [![CircleCI](https://cci.gamma.bcg.com/gh/BCG/gamma-config/tree/develop.svg?style=shield&circle-token=8106c47ad7a019907079adc538ec98b9ba6b0e95)](https://cci.gamma.bcg.com/gh/BCG/gamma-config/tree/develop "develop")

An opinionated way of setting up configuration for data science projects.

## Overview

Gamma config provides a standard and flexible way of implementing application
configuration primarily based on YAML files. It promotes best practices by:

-   simplify separation of code and config data;
-   breaking large, complex configuration into multiple files;
-   providing a way to write environment-aware config files;
-   facilitating security best-practices, like proper secrets management;
-   providing a immutable central global object storing **all** contextual data.

Another benefit of a standard config mechanism is allowing Gamma extension
libraries to provide configuration in a common way.

## Features

-   Configuration expressed as a set of YAML files (by defaul) inside a
    `config` folder in the root of the project.
-   Multiple YAML files merged following simple rules. Simple file ordering convention
    using two digit prefixes.
-   Builtin support for environment specific parameters (production, development, etc.)
-   Support for `.env` files via `python-dotenv`, including `.local.env` that
    can be added to `.gitignore`
-   Dynamic evaluation via YAML tags. For instance, the `!ref` tag allow you to
    reference other parameters in any config file.
-   Custom tag support via simple and cool multiple dispatch mechanism.
-   Round-trip dump of config back into YAML. Support for hiding sensitive data
    on dump.
-   Simplified key access via dot (`.`). Eg. for `config: {foo: {bar: 100}}`,
    this is True: `config.foo.bar == 100`

## Full documentation

Link: https://github.gamma.bcg.com/pages/BCG/gamma-config/

## Getting started

Currently the recommended way of installing `gamma-config` is downloading the `tar.gz`
asset file in the [Releases](https://github.gamma.bcg.com/BCG/gamma-config/releases)
and install it using `pip`.

```bash
pip install ./gamma-config-<release>.tar.gz
```

To use it in your project, you can place the _tar.gz_ files in a `vendor` folder and
reference it either via pip's `-f` flag or by setting `PIP_FIND_LINKS` env var:

```bash
# requirements.txt:
gamma-config

# then explicity set -f (--find-links) flag
pip install -r requirements.txt -f ./vendor
```

Poetry currently does not support the equivalent of `--find-links` so you may need to
explicity add the path/version to `pyproject.toml`

```toml
[tool.poetry.dependencies]
gamma-config = { path = "./vendor/gamma-config-<release>.tar.gz" }
```

This technique is called "vendoring" the dependency. For client work this also
provides the library source should they wish to modify it later.

In most cases, you'll want to use the `!j2` tag to interpolate values using Jinja2.
This requires manually installing the `jinja2` package or using the `jinja2` extras.

```bash
# when using pip
pip install gamma-config[jinja2]
```

## Basic Usage

The package comes with "scaffolding" to help you get started. In your project folder:

```bash
   python -m gamma.config.scaffold
```

Remove the sample files, then create yourself a `config/20-myconfig.yaml` file
with the contents:

```yaml
foo: 1
user: !env USER
```

To access the config from within your Python program:

```python
import os
from gamma.config import get_config

def run():

    # it's safe and efficient to call this multiple times
    config = get_config()

    # get static value using the dict keys or attribute access
    assert config["foo"] == 1
    assert config.foo == 1

    # get dynamic variables
    assert config["user"] == os.getenv("USER")
    assert config.user == os.getenv("USER")
```

Most of the magic happen via tags. Look at the documentation for info on the [built-in tags](tags) available.

## Copyright

Copyright 2021 Boston Consulting Group, all rights reserved.
