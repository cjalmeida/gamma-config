import os
from pathlib import Path

import pytest
from beartype.typing import NamedTuple

from gamma.config import RootConfig, ScalarNode, render_node, to_dict
from gamma.config.builtin_tags import RefTag


def test_ref():
    # simple access
    root = RootConfig("dummy", {"foo": {"bar": 100}})
    node = ScalarNode("!ref", "foo.bar")
    val = render_node(node, RefTag(), config=root)
    assert val == 100

    # quoted access
    root = RootConfig("dummy", {"hello.world": {"bar": 100}})
    node = ScalarNode("!ref", "'hello.world'.bar")
    val = render_node(node, RefTag(), config=root)
    assert val == 100


def test_ref_sibling():
    src = """
    a: foo
    b:
      ref_a: !ref a
      sib: !ref b.ref_a
    """

    cfg = RootConfig("dummy", src)
    assert cfg["b"]["ref_a"] == "foo"
    assert cfg["a"] == "foo"
    assert cfg["b"]["sib"] == "foo"


def test_ref_to_dict():
    src = """
    a: foo
    c:
      sub: bar
    b:
      ref_a: !ref a
      sib: !ref b.ref_a
      ref_c: !ref c
    """

    cfg = RootConfig("dummy", src)
    d = to_dict(cfg, recursive=True)
    assert d["b"]["ref_a"] == "foo"
    assert isinstance(d["b"]["ref_c"], dict)


class MyObj(NamedTuple):
    val: dict


class MyObj2(NamedTuple):
    a: int
    b: int


def make_double(val):
    return [2 * x for x in val]


def make_list(val):
    return [val]


def hello():
    return "world"


def test_py_tag():
    mod = __name__
    src = f"""
    foo: !py:{mod}:MyObj
        a: !py:{mod}:make_list 1
        b: !py:{mod}:make_double
            - 2
    hello: !py:{mod}:hello
    """

    cfg = RootConfig("dummy", src)
    foo = cfg["foo"]
    assert isinstance(foo, MyObj)
    assert isinstance(foo.val, dict)
    assert foo.val["a"] == [1]
    assert foo.val["b"] == [4]
    assert cfg["hello"] == "world"


def test_exceptions():
    mod = __name__

    with pytest.raises(Exception, match="invalid reference"):
        cfg = RootConfig("dummy", f"hello: !py:{mod}.hello")
        assert cfg["hello"] == "world"

    with pytest.raises(Exception, match="missing"):
        cfg = RootConfig("dummy", f"hello: !py {mod}.hello")
        assert cfg["hello"] == "world"

    with pytest.raises(Exception, match="not found"):
        cfg = RootConfig("dummy", "hello: !py:wrong_module:hello")
        assert cfg["hello"] == "world"

    with pytest.raises(Exception, match="not found"):
        cfg = RootConfig("dummy", f"hello: !py:{mod}:wrong_function")
        assert cfg["hello"] == "world"


def test_obj_tag():
    mod = __name__
    src = f"""
    obj_default_module: {mod}

    foo: !obj:MyObj2
        a: 1
        b: 2

    bar: !obj:{mod}:hello
    zee: !obj:{mod}:make_list 1
    """

    cfg = RootConfig("dummy", src)
    foo = cfg["foo"]
    assert isinstance(foo, MyObj2)
    assert foo.a == 1
    assert foo.b == 2
    assert cfg["bar"] == "world"
    assert cfg["zee"] == [1]


def test_path_tag():
    # construct paths for testing non-OS-specific:
    test_path = os.path.join("testdir", "testfile")
    test_path_fragment = os.path.join(os.pardir, test_path)

    src = f"""
    foo: !path ..{test_path_fragment}
    """

    foo = RootConfig("dummy", src)["foo"]

    assert str(foo).endswith(test_path_fragment)
    assert Path(foo).is_absolute()


def _custom_j2_env():
    from jinja2 import Environment

    return Environment()


def test_j2_env():
    from gamma.config.builtin_tags import j2_cache

    src = """
    j2_env: %(mod)s:_custom_j2_env
    myval: !j2 "{{ 2 + 2 }} = 4"
    """ % {
        "mod": __name__
    }

    try:
        # remove j2 env cache
        if hasattr(j2_cache, "env"):
            del j2_cache.env

        cfg = RootConfig("dummy", src)
        myval = cfg["myval"]
        assert myval == "4 = 4"

    finally:
        if hasattr(j2_cache, "env"):
            del j2_cache.env


def test_j2_strict():
    src = """
    myok: !j2 "hello {{ 'world' }}"
    myval: !j2 "{{ foo }} = foo"
    """
    cfg = RootConfig("dummy", src)

    assert cfg["myok"] == "hello world"

    with pytest.raises(ValueError, match="render"):
        cfg["myval"]
