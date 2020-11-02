===================
Loading and merging
===================

By default, we'll delay loading anything until the first call to ``get_config()`` is
made. Then we'll procede to select all `*.yml` and `*.yaml` files in the
:ref:`meta-config-root` and folders pointed by the ``include_folders`` parameter in
``00-meta.yaml`` file. Note we **will not recursively** process files in those folders.

All config files are then collected and **sorted by file name** for processing.
For this reason, by convetion we prefix config files with a two digit number to make
it clear the loading order.


Strategic merging
-----------------

The YAML files are parsed and converted to Python *dicts*, then merged using a simple
algorithm. So it's important to note that the order of merge matters, thus the file
name when using the default loader.

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
            "key_b": "new",
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

