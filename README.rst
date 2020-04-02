============
Gamma Config
============

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


Getting started
~~~~~~~~~~~~~~~

Install the latest stable version using ``pip``. You need to setup SSH access
to ``git.sourceai.io`` for now:

::

    pip install ssh://git@git.sourceai.io/devex-br/gamma-config.git@v0.1.0

Or, when adding to ``requirements.txt``

::

    gamma-config @ git+ssh://git@git.sourceai.io/devex-br/gamma-config.git@v0.1.0#egg=gamma-config


The dependency above install and extends the ``gamma`` CLI command. After installation
you can "scaffold" a new config folder with samples using

::

    gamma config scaffold

Basic Usage
~~~~~~~~~~~

Configuration loading
#####################

The ``gamma config scaffold`` command will generate a ``config/`` folder with a couple
of YAML files. The ``00-meta.yaml`` is a "eat your own dogfood" config file where we
configure *gamma-config* itself. You mostly don't have to deal with it.

After the "meta" phase of config loading, any other YAML file is loaded, including
environment overrides. We provide by default sample ``dev`` and ``prod`` environments.
The environment to use is set in the ``environment`` entry in the ``00-meta.yaml`` file.
By default it tries to load from the ``ENVIRONMENT`` system environment variable.

The YAML files are parsed and converted to Python dicts, then merged using a simple
algorithm. It's important to note that the order of merge matters, so we sort the
config files by name adn ensure proper ordering by prefixing them with two digits -
a common UNIX convention.

For example:

**config/10-foo.yaml**

.. code-block:: yaml

    sample_key:
        key_a: foo
        key_b: old
        key_c: [1, 2]

**config/15-bar.yaml**

.. code-block:: yaml

    sample_key:
        key_b: old
        key_c: [2, 3]
        key_d: bar

After loading the two files above, the result config will contain:

.. code-block:: python

    {
        "sample_key": {
            "key_a: "bar",
            "key_b": "new,
            "key_c": [1, 2, 3],
            "key_d": "bar"
        }
    }

Using gamma-config in your code
###############################

To use the loaded config in your code simply import and call the ``get_config``
function, like in the example below:

.. code-block:: python

    from gamma.config import get_config

    config = get_config()
    assert config["sample_key"]["key_a"] == "bar"
    assert config["sample_key"]["key_c"] == [1, 2, 3]


Advanced Usage
~~~~~~~~~~~~~~

Builtin Tags
############

The library can be extended by using YAML tags. We provide a couple of them to achieve
basic functionality:

!env
----

References a system environment variable. **Do not use this tag to load secrets** as
the contents are dumped by default on the ``to_yaml()`` call. You can use the ``|``
(pipe) character to provide a default if a value is missing.

Example:

.. code-block:: yaml

    sample_key:
        my_var: !env VAR|my_default


!env_secret
-----------

Similar to ``!env`` but won't dump the variable contents.

Example:

.. code-block:: yaml

    sample_key:
        my_var: !env_secret SECRET|my_secret

!ref
----

References another entry in the config object, even if it's in another file or
overriden by an environment specific entry.

Example:

.. code-block:: yaml

    key_a:
      sub_key: 100

    # use dot notation to access nested entries
    # will be the same as key_a -> subkey == 100
    key_b: !ref key_a.sub_key


!expr
-----

Allows you to evalute arbitrary Python expressions, using the ``eval()`` builtin. The
objects available in the expression evaluation context can extended using a plugin
hook implementation.

Example usage:

.. code-block:: yaml

    sample_key:
        # we may need to enclose the whole expression in quotes
        my_var: !expr '"This is an env variable" + env["USER"]'


Example globals extending plugin implementation:

.. code-block:: python

    import os
    from gamma.config import plugins

    @plugins.hookimpl
    def expr_globals():
        return {"env": os.environ}

    plugins.plugin_manager.register(sys.modules[__name__])
