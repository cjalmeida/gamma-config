============
Gamma Config
============


>> **Note**: This repository is archived. Please find it in the new home at 
https://github.gamma.bcg.com/BCG/gamma-config


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

Currently the release packages are installed under the `devex-br` private Artifactory
repository. To configure your access to it:

1. Open your `Artifactor Profile Page <https://artifactory.gamma.bcg.com/artifactory/webapp/#/profile>`_
2. Generate or copy your API Key
3. Update your `pip` installation if needed
   ::

       pip install --upgrade pip

4. Run the command below to configure `pip` to use the repo. Replace `<name>` with the
   first part of your BCG email.
   ::

       pip config --user set global.extra-index-url https://<name>%40bcg.com:<api_key>@artifactory.gamma.bcg.com/artifactory/api/pypi/local-pypi-8999823-devex-br-01/simple

You should be able to install the latest released version using ``pip``.

::

    pip install gamma-config

The package comes with "scaffolding" to help you get started. If you have ``gamma-cli``
installed, you can run ``gamma config scaffold`` or ``python -m gamma.config scaffold``
otherwise.

Basic Usage
~~~~~~~~~~~

Configuration loading
#####################

The ``scaffold`` command will generate a ``config/`` folder with a couple
of YAML files. The ``00-meta.yaml`` is a "eat your own dogfood" config file where we
configure *gamma-config* itself. You mostly don't have to deal with it.

After the "meta" phase of config loading, any other YAML file is loaded, including
environment overrides. We provide by default sample ``dev`` and ``prod`` environments.
The environment to use is set in the ``environment`` entry in the ``00-meta.yaml`` file.
By default it tries to load from the ``ENVIRONMENT`` system environment variable.

Strategic merging
-----------------

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
        key_d:
          foo: 10
          bar: 20

**config/15-bar.yaml**

.. code-block:: yaml

    sample_key:
        key_b: new
        key_c: [2, 3]
        key_d:
          foo: 15
        key_e: inserted


After loading the two files above, the result config will contain:

.. code-block:: python

    {
        "sample_key": {
            "key_a: "bar",
            "key_b": "new,
            "key_c": [1, 2, 3],
            "key_d": {"foo": 15, "bar": 20},
            "key_e": "inserted"
        }
    }

If you want change this behavior, you can pass special "parser hints" comments.
Currently we implement the ``@hint: merge_replace`` hint to fully replace the key value
instead of trying to merge lists/maps.

The ``@hint`` comment must be placed on the same line of the key you want to it to act.

Same example as above, but with the ``merge_replace`` hints:


**config/10-foo.yaml**

.. code-block:: yaml

    sample_key:
        key_a: foo
        key_b: old
        key_c: [1, 2]
        key_d:
          foo: 10
          bar: 20

**config/15-bar.yaml**

.. code-block:: yaml

    sample_key:
        key_b: new
        key_c: [2, 3]  # @hint: merge_replace
        key_d:  # @hint: merge_replace
          foo: 15
        key_e: inserted

And the output:

.. code-block:: python

    {
        "sample_key": {
            "key_a: "bar",
            "key_b": "new,
            "key_c": [2, 3],
            "key_d": {"foo": 15},
            "key_e": "inserted"
        }
    }




Dotenv (.env) Support
---------------------

By default, config will try to load the files ``config.env`` and ``config.local.env``,
one after another. The expected pattern is to commit ``config.env`` in your VCS (Git)
and leave ``config.local.env`` for user specific configuration.

Note the ``.env`` files are loaded by simply doing an ``import gamma.config`` even
before the meta configuration loading.

Using gamma-config in your code
###############################

To use the loaded config in your code simply import and call the ``get_config``
function, like in the example below:

.. code-block:: python

    from gamma.config import get_config

    config = get_config()
    assert config["sample_key"]["key_a"] == "bar"
    assert config["sample_key"]["key_c"] == [1, 2, 3]


Attribute access
----------------

Most of the time, you can access the keys using dot ``.`` notation. For instance, given

.. code-block:: yaml

    sample_key:
        key_b: old
        key_c: [2, 3]
        key_d: bar

The following should not raise any errors:

.. code-block:: python

    from gamma.config import get_config

    config = get_config()
    assert config.sample_key.key_a == "bar"
    assert config.sample_key.key_c == [1, 2, 3]

    # default dict behavion
    assert not config.sample_key.bogus
    assert not config.sample_key.bogus.subkey

Limitations:
  * When using attribute access, non existing keys will always return an empty ``Config`` dict
    allowing "safe" navigation. Thus, the ``is None`` check will fail, use the regular
    dictionary access if you need more strict semantics.

  * As expected, ``Config`` class methods, like `dump`, `pop`, `push`, `to_yaml`, etc.,
    get preference. We don't guarantee we won't break your code in the future by
    implementing new functionality.

  * We don't support attribute access for keys starting with underscore (``_``) at all.

  * The attribute access may interfere with some serialization algorithms or other
    processes. If you see weird behavior, you can disable it by setting
    ``config._allow_dot_access`` to ``False``.


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


Developing
~~~~~~~~~~

Relevant environment variables
##############################

PROJECT_HOME
------------

You can set the ``PROJECT_HOME`` environment variable to define the "home" location
where the default config loaders should expect the ``config/`` folder to be. This is
useful in testing and scripts.
