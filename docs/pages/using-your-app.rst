===============================
Using gamma-config in your code
===============================

To use the loaded config in your code simply import and call the ``get_config``
function, like in the example below:

.. code-block:: python

    from gamma.config import get_config

    config = get_config()
    assert config["sample_key"]["key_a"] == "bar"
    assert config["sample_key"]["key_c"] == [1, 2, 3]

Getting raw dicts
-----------------

Assume the configuration below:

.. code-block:: yaml

    root:
      sub:
        key_a: !env USER
        key_b: [1, 2, 3]


The value of ``config["sub"]`` is a *dict-like* data structure but due to it's dynamic
nature it's not a true Python ``dict`` and may fail in situations where dicts are
expected - in particular in multiple serializaion scenarios.

In those situations, you can call ``config.to_dict()`` to resolve the dynamic data
structure to a plain Python ``dict``. Thus:

.. code-block:: python

    config.sub.to_dict() == {"key_a": "myuser", "key_b": [1, 2, 3]}





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
