===============
Getting started
===============

Currently the recommended way of installing gamma-config is downloading the *whl*
asset file in the `Releases <https://github.gamma.bcg.com/BCG/gamma-config/releases>`_
and install it using ``pip``.

.. code-block:: bash

    pip install ./gamma_config-<release>-py3-none-any.whl

To use it in your project, you can place the *whl* files in a ``wheels`` folder and
reference it either via pip's ``-f`` flag or by setting ``PIP_FIND_LINKS`` env var:

.. code-block:: bash

    # explicity set -f (--find-links) flag
    pip install gamma-config -f ./wheels

The package comes with "scaffolding" to help you get started. If you have ``gamma-cli``
installed, you can run ``gamma config scaffold`` or ``python -m gamma.config scaffold``
otherwise.


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
