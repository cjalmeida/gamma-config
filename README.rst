============
Gamma Config
============

|badge_python|

Provides an opinionated way of setting up complex configuration for BCG Gamma pipelines.

Why?
~~~~

There are multiple ways of configuring an application. I believe that providing an
standard way of implementing app configuration reduces the cognitive burden on fellow
data scientists while promoting best practices.

**Isn't just using a plain YAML file enough?** Yes, and no. To minimize confusion and
help reproducibility we stick to the principle that **all** configuration parameters
should be reflected as part of the global object returned by ``get_config``. That
include stuff such as secrets, deployed configuration, CLI parameters,
external configuration, glue-code parameters, etc. By experience, you simplify a lot
of stuff moving these concerns from the application itself to a declarative
configuration layer.

Another reason is to provide a foundation to configure plugins in a declarative but
decentralized way.

Core features
~~~~~~~~~~~~~

* By default, the configuration is expressed as a set of YAML 1.2 files inside a
  ``config`` folder in the root of the project.

* The multiple YAML files are parsed as a Python dictionary-like object and merged
  following simple rules. The order of merging files matter.

* Builtin support for environment specific parameters (production, development, etc.)

* Support for ``.env`` files via ``python-dotenv``.

* The feature set can be extended through the use of YAML tags. For instance, the
  ``!ref`` tag allow you to reference other parameters in the config file.

* Support for plugins (via pluggy) extending functionality.

* Round-trip dump of config dict back into YAML. Support for hiding sensitive data
  on dump.

* Simplified key access via dot (``.``). Ie. for  ``config: {foo: {bar: 100}}``,
  this is True: ``config.foo.bar == 100``

Documentation
~~~~~~~~~~~~~

Link: https://github.gamma.bcg.com/pages/BCG/gamma-config/latest/

Getting started
~~~~~~~~~~~~~~~

Currently the recommended way of installing gamma-config is downloading the *whl*
asset file in the `Releases <https://github.gamma.bcg.com/BCG/gamma-config/releases>`_
and install it using ``pip``.

::  code-block:: bash

    pip install ./gamma_config-<release>-py3-none-any.whl

To use it in your project, you can place the *whl* files in a ``wheels`` folder and
reference it either via pip's ``-f`` flag or by setting ``PIP_FIND_LINKS`` env var:

:: code-block:: bash

    # explicity set -f (--find-links) flag
    pip install gamma-config -f ./wheels


Basic Usage
~~~~~~~~~~~

The package comes with "scaffolding" to help you get started. In your project folder:

.. code-block:: bash

   python -m gamma.config scaffold

Then create yourself a ``config/20-myconfig.yaml`` file with the contents:

.. code-block:: yaml

   foo: 1
   user: !env USER

To access the config from within your Python program:

.. code-block:: python

    import os
    from gamma.config import get_config

    def run():

        # it's safe and efficient to call this multiple times
        config = get_config()

        # get static value using the dict interface
        assert config["foo"] == 1

        # or using attribute access
        assert config.foo == 1

        # get dynamic variables
        assert config["user"] == os.getenv("USER")
        assert config.user == os.getenv("USER")

Most of the magic is done using. Look at the documentation for info on the tags
available.


.. |badge_python| image:: https://img.shields.io/badge/python-3.6%2B-blue
  :alt: python version
