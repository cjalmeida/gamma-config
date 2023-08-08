# Gamma Config

![python](https://img.shields.io/badge/python-3.8%2B-blue) ![build](https://github.com/cjalmeida/gamma-config/actions/workflows/build-deploy.yaml/badge.svg) ![cov](https://img.shields.io/badge/coverage-91%25-green)

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

[Click here to view the full documentation](https://cjalmeida.github.io/gamma-config/)

## Getting started

Using pip:

```bash
pip install gamma-config
```

In most cases, you'll want to use the `!j2` tag to interpolate values using Jinja2.
This requires manually installing the `jinja2` package or using the `jinja2` extras.

```bash
pip install gamma-config[jinja2]
```

You must install `pydantic` if using the [structured configuration][structured] feature.

```bash
pip install gamma-config[pydantic]
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

## Changelog

### Breaking in 0.6

-   Strict support for [YAML 1.2 Core Schema](https://yaml.org/spec/1.2.1/#id2804923).
    In practice, unquoted ISO8610 dates (eg. `2022-12-20`) won't get converted
    to `datetime.date` or `datetime.datetime` objects. Use `!date` or `!datetime`
    if needed.
-   `.env` files are loaded automatically and get precedence over `config.env`
    and `config.local.env`.
-   Use of `config.env` and `config.local.env` is deprecated.
-   Default scaffolded `include_folder` interpret `ENVIRONMENT` variable string like
    `foo bar` as two separate environment subfolders.
-   (dispatch) `Val` arguments passed as class (eg. `foo(Val['bar'])`) will be converted
    to instance, as if it were called `foo(Val['bar']())`
-   The `!py:<module>:<func>` will no longer a single `None` argument

### New in 0.6

-   Support for [YAML Anchors and Aliases](https://www.educative.io/blog/advanced-yaml-syntax-cheatsheet#anchors)

### New in 0.5

-   We're now in PyPI!
-   Options for installing extra dependencies (eg. `jinja2`, `pydantic`)

### Breaking changes in 0.5

-   When using the dot (`.`) syntax, missing values raise `AttributeError` instead of returning
    a false-y object.
-   Dropped support for Python 3.7

## Copyright

Copyright 2021 Boston Consulting Group, all rights reserved.

[structured]: https://github.gamma.bcg.com/pages/BCG/gamma-config/structured
