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

* Round-trip dump of config dict back into YAML. Support for hiding sensitive data
  on dump.

* Simplified key access via dot (``.``). Ie. for  ``config: {foo: {bar: 100}}``,
  this is True: ``config.foo.bar == 100``


Getting started
~~~~~~~~~~~~~~~

Currently the recommended way of installing gamma-config is downloading the *whl*
asset file in the `Releases <https://github.gamma.bcg.com/BCG/gamma-config/releases>`_
and install it using ``pip``.

::  code-block: bash

    pip install ./gamma_config-<release>-py3-none-any.whl

To use it in your project, you can place the *whl* files in a ``wheels`` folder and
reference it either via pip's ``-f`` flag or by setting ``PIP_FIND_LINKS`` env var:

:: code-block: bash

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

!func
-----

Returns a reference to a function. Useful for lightweight dependency injection.

Example usage:

.. code-block:: yaml

    # call using kwargs
    func_3: !func
      call: os:getenv                 # <module>:<func>
      args: ["MISSING"]               # list of positional arguments
      kwargs: {default: foo}          # map of keyword arguments

The above will return a "partial" reference to ``os.getenv``. This is equivalent to
``functools.partial(os.getenv, "MISSING", default="foo")``


!option
-------

Enables you to reference a **Click** ``@click.option`` in your configuration.

To capture an option, use ``gamma.config.cli.option`` decorator as a drop-in replacement
for ``click.option``. This accept default values in config using the
``|`` (pipe) separator.

Example:

Define your command line using **Click** as usual:

.. code-block:: python

    import click
    from gamma.config.cli import option

    @click.command()
    @option('-m', '--myarg')
    @option('-o', '--otherarg')
    def my_command(myarg, otherarg):
        """do something"""


And in the configuration

.. code-block:: yaml

    sample_key:
        my_arg: !option myarg
        other: !option otherarg|other
        unset: !option unset|mydefault


When calling your script with ``myscript.py --myarg foo``, should result in:

.. code-block:: python

    from gamma.config import get_config

    config = get_config()
    assert config["sample_key"]["myarg"] == "foo"
    assert config["sample_key"]["otherarg"] == "other"
    assert config["sample_key"]["unset"] == "mydefault"

Note: The ``@option`` default of ``None`` is handled as "unset value". This means that
you must either provide a non-``None`` default to your option or provide a ``|default``
to your configuration.


!j2 / !j2_secret
----------------

Allow the use of Jinja2 templates.  The context for rendering is shared with the
``!expr`` and can be extended with the same ``expr_globals`` plugin hook.

In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

    myvar: 100
    foo1: !expr f"This is a number = {c.myvar}"
    foo2: !j2 This is a number = {c.myvar}

We also provide `!j2_secret` to be used when dealing with sensitive data

Note that  Jinja2 **is not installed by default**, you should install yourself by
running `pip install jinja2`.


!dump_raw
---------

Instruct the dumper that the entire configuration block should not have the !tags
resolved. This is useful if you have dynamic or expensive functions being called that
you don't want rendered when dumping.

Example. Given the config snippet below:

.. code-block:: yaml

    raw: !dump_raw
        bar: !j2 "{{ env.USER }}"

    normal:
        bar: !j2 "{{ env.USER }}"

Calling ``config.to_yaml()`` should output this:

.. code-block:: yaml

    raw: !dump_raw
        bar: !j2 "{{ env.USER }}"

    normal:
        bar: myuser

