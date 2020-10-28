Welcome to gamma-config's documentation!
========================================


This package provides an opinionated way of setting up complex configuration for
data applications.

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

Another reason is to provide a foundation that plugins and even other projects in
BCG Gamma tooling ecossystem can use to setup configuration in a declarative and
stop re-inventing the wheel.

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

* Simplified key access via dot (``.``). Eg. for ``config: {foo: {bar: 100}}``,
  this is True: ``config.foo.bar == 100``


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   pages/getting-started
   pages/meta-config
   pages/loading-merging
   pages/using-your-app
   pages/tags

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
