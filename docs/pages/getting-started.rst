===============
Getting started
===============


Currently the recommended way of installing ``gamma-config`` is downloading the ``tar.gz``
asset file in the `Releases <https://github.gamma.bcg.com/BCG/gamma-config/releases>`_
and install it using ``pip``.

.. code-block:: bash

    pip install ./gamma-config-<release>.tar.gz

To use it in your project, you can place the *tar.gz* files in a ``vendor`` folder and
reference it either via pip's ``-f`` flag or by setting ``PIP_FIND_LINKS`` env var:

.. code-block:: bash

    # requirements.txt:
    gamma-config

    # then explicity set -f (--find-links) flag
    pip install -r requirements.txt -f ./vendor

Poetry currently does not support the equivalent of ``--find-links`` so you may need to
explicity add the path/version to ``pyproject.toml``

.. code-block:: toml

    [tool.poetry.dependencies]
    gamma-config = { path = "./vendor/gamma-config-0.2.14.tar.gz" }


This technique is called "vendoring" the dependency. For client work this also
provides the library source should they wish to modify it later.

In most cases, you'll want to use the ``!j2`` tag to interpolate values using Jinja2.
This requires manually installing the ``jinja2`` package

.. code-block:: bash

    pip install "jinja2==2.*"

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

Most of the magic is done using YAML tags like ``!env`` above. Look at the
:ref:`tags` section for info on the tags available.
