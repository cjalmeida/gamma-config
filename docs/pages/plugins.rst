.. _plugins:

=======================
Plugins and Custom Tags
=======================

While you can do a lot with the built-in tags, most of the time you'll want to augment
them with custom tags or extra variables in your ``expr/j2`` evaluation context. In
this section we'll see some ways to achieve this.

We leverage the `Pluggy <https://pluggy.readthedocs.io/en/latest/>`_ plugin system to
provide a structured approach to extending *gamma-config*.


How it works
------------

When we read your YAML files, ``!tag`` nodes are like regular nodes except their
values (along with some context) are passed through *tag handler functions*. Those tag
handler are functions that accept a particular set of arguments and return a value.

Those functions are called **at the time of key/attribute** access, not when loading
the config files.


.. _plugins-custom-app-tags:

Custom application tags
-----------------------

Adding custom tags to your applicaiton (also called *application tags*) requires:

a) Creating a *tag handler* function;
b) Adding the function as a ``TagSpec`` in the ``application_tags`` global;
c) Modifying your ``00-meta.yaml`` to auto-load the module;

In your application code (we'll call it ``myapp``) create a ``myplugin.py`` file:

.. code-block:: python

    # file: myapp/myplugin.py

    # let's load the gamma-config plugins module
    import os, sys
    from gamma.config import plugins


    # create a tag handler for !myenv
    def myenv(value):
        """Simplified !env tag without default handling"""

        env_val = os.getenv(value)
        return env_val

    # register in application_tags global
    plugins.application_tags.append(plugins.TagSpec("!myenv", myenv))


And in the ``00-meta.yaml`` file just add:

.. code-block:: yaml

    plugins:
      modules: ["myapp.myplugin"]


You should then be able to use ``!myenv`` in your config files.


Using the plugin subsystem
--------------------------

The `Pluggy <https://pluggy.readthedocs.io/en/latest/>`_ plugin system is aimed at
library developers that want to extend gamma-config and automatically load your
custom tags.

In summary, the steps are:

a) Creating a *tag handler* function inside a custom plugin Python module;
b) Mapping the function to a tag by creating a *plugin hook implementation* function;
c) Call ``plugin_manager.register`` to register your Python module as a plugin
   implementation;
d) Setup an entrypoint to your package.

For example, in your application code (we'll call it ``myapp``) create a
``myplugin.py`` file:

.. code-block:: python

    # file: myapp/myplugin.py

    # let's load the gamma-config plugins module
    import os, sys
    from gamma.config import plugins

    # create a tag handler for !myenv
    def myenv(value):
        """Simplified !env tag without default handling"""

        env_val = os.getenv(value)
        return env_val


    # Create a "hookimpl" to register the tag. The hookimpl *must* be named "add_tags"
    @plugins.hookimpl
    def add_tags():
        """Add custom tags to gamma-config"""

        # you can have multiple "TagSpec" here.
        return [
            plugins.TagSpec("!myenv", myenv),
        ]

    # register the current module as a plugin source
    plugins.plugin_manager.register(sys.modules[__name__])

There are many ways to setup an entrypoint, here you can find the full `Entry points specification <https://packaging.python.org/specifications/entry-points/>`_
from official *Python Packaging* docs. If you're using *setuptoools* a typical
configuration would be:

.. code-block:: python

    setup(
        ...,                                # the rest of your setup spec
        entry_points = {
            "gamma.config": [               # the "group" must be 'gamma.config'
                "myapp = myapp.myplugin",   # the "object reference" must be the plugin module
            ],
        },
    )
