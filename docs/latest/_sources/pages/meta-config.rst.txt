===============================
Configuring gamma-config itself
===============================

.. _meta-config-root:

Root config folder
------------------

When ``get_config()`` is first called, it initializes the configuration loading by
looking for a ``00-meta.yaml`` file in the so-called "root" folder. By default, the
root folder is resolved from these locations:

*  The absolute path in ``GAMMA_CONFIG_ROOT`` env var if set.
*  ``$PWD/config``.
*  When running under a IPython kernel (ie. Jupyter), any parent folder that may
   have a ``config/00-meta.yaml`` file.

If you have specific packaging needs, we recommend you set the ``GAMMA_CONFIG_ROOT``
environment variable in your application entrypoint script using ``os.setenv``.

.. important::

    While it's OK to call ``get_config()`` from anywhere when exploring using Jupyter
    notebooks, when writing an application we recommend you never do it outside of a
    function to void risking initializing your config as part of loading
    module code (ie. as a side-effect of a ``import`` call).

Dotenv support
--------------

After finding the "root" as described above, the code tries to some specific "dotenv"
files:

*  ``{config_root}/../config.local.env``
*  ``{config_root}/../config.env``

The variables loaded in this fashion can be used anywhere in the code, in particular
using the ``!env`` config tag.

.. note::
    When using *gamma-config* we strongly discourage extensive use of environment
    variables. Instead see if the :ref:`meta-include-folders` feature can be used to
    store environment specific static configuration.

    In case of secrets, use the ``!func`` tag or a dedicated plugin to store those
    in "vault" systems like *Hashicorp Vault* or *Azure Key Vault*.


The "00-meta.yaml" file
-----------------------

The ``00-meta.yaml`` is a "eat your own dogfood" config file where we
configure *gamma-config* itself. The default provided one is pretty sane so you
mostly don't have to deal with it.

Check the next sessions for details on the meta parameters.

.. _meta-include-folders:

Include extra folders
++++++++++++++++++++++

Meta parameter: ``include_folders``

All YAML files in the root folder and entries in the ``include_folders`` parameter
are marked for loading. The default ``00-meta.yaml`` file provides by default a
dynamic entry resolving to the ``ENVIRONMENT`` variable. We use this to (optionally)
override the default configuration with environment specific parameters.

.. note::
    The final loading order is determined by the file **name**, all other path parts are
    stripped out.

Plugin modules auto-import
++++++++++++++++++++++++++

Meta parameters: ``plugins.modules``

Modules names here will be automatically import. The common use-case is to use this to
automatically add application tags to ``gamma.config.plugins:applications_tags`` list.
See :ref:`plugins-custom-app-tags` for more details.
