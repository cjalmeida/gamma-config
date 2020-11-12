.. _tags:

===============================
Dynamic configs with YAML !tags
===============================

We believe *gamma-config* is a good step in the direction of achieving proper
separation of concerns in data science applications. The way it does is by
providing a rich set of directives (ie. YAML tags) that allows engineers to specify
high-level abstractions to data scientists, allowing DS to focus on solving the
core modeling problems while worring less about the underlying infrastructure.

We provide a core set of built-in tags to make your config files more dynamic, but
we allow you to extend it in your own application, check the :ref:`plugins` section
for more info.


Built-in Tags
#############


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
      ref: os:getenv                # <module>:<callable>
      args: ["MISSING"]             # list of positional arguments
      kwargs: {default: foo}        # map of keyword arguments
      call: true                    # run function on access

Argument reference:

-   ``ref``, a reference to a callable in the form ``<module>:<callable>``
-   ``args``, optional positional args
-   ``kwargs``, optional keyword args
-   ``call``, if false (default) accessing the config entry returns a "partial",
    otherwise it calls the function and returns the result


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
    from gamma.config.cli import option as config_option

    @click.command()
    @config_option('-m', '--myarg')
    @config_option('-o', '--otherarg')
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

.. important::

    The ``@config_option`` default of ``None`` is handled as "unset value". This means that
    you must either provide a non-``None`` default to your option or provide a ``|default``
    to your configuration.

.. note::
    The way we implement it is by setting a special ``GAMMA_CONFIG_OPTIONS`` environment
    variable. If you're relying on passing down ``gamma-config`` to child processes
    (eg. when using ``subprocess`` module) make sure to pass down at least this
    environment variable.


!j2 / !j2_secret
----------------

Allow the use of Jinja2 templates.  The context for rendering is shared with the
``!expr`` and can be extended with the same ``expr_globals`` plugin hook.

In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

.. code-block:: yaml

    myvar: 100
    foo1: !expr f"This is a number = {c.myvar}"
    foo2: !j2 This is a number = {c.myvar}

We also provide ``!j2_secret`` to be used when dealing with sensitive data

.. important::
    Jinja2 **is not installed by default**, you should install yourself by
    running ``pip install jinja2``.


!dump_raw
---------

Instruct the dumper that the entire configuration block should not have the **!tags**
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




