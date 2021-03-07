from typing import NamedTuple
from gamma.config import RootConfig, ScalarNode, render_node
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
    assert cfg.b.ref_a == "foo"
    assert cfg.a == "foo"
    assert cfg.b.sib == "foo"


class MyObj(NamedTuple):
    val: dict


class MyObj2(NamedTuple):
    a: int
    b: int


def make_double(val):
    return [2 * x for x in val]


def make_list(val):
    return [val]


def test_py_tag():
    mod = __name__
    src = f"""
    foo: !py:{mod}:MyObj
        a: !py:{mod}:make_list 1
        b: !py:{mod}:make_double
            - 2
    """

    foo = RootConfig("dummy", src).foo
    assert isinstance(foo, MyObj)
    assert isinstance(foo.val, dict)
    assert foo.val["a"] == [1]
    assert foo.val["b"] == [4]


def test_obj_tag():
    mod = __name__
    src = f"""
    obj_default_module: {mod}

    foo: !obj:MyObj2
        a: 1
        b: 2
    """

    foo = RootConfig("dummy", src).foo
    assert isinstance(foo, MyObj2)
    assert foo.a == 1
    assert foo.b == 2
