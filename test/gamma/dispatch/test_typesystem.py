import typing
from typing import Tuple, Union

from gamma.dispatch.typesystem import Sig, SigSet, Vararg, is_more_specific, issubtype


class SuperFoo:
    pass


class Foo(SuperFoo):
    pass


class SuperBar:
    pass


class Bar(SuperBar):
    pass


def test_partial_order_unary():
    foo = Tuple[Foo]
    base = Tuple[SuperFoo]
    other = Tuple[SuperBar]
    obj = Tuple[object]

    assert issubtype(foo, obj)
    assert issubtype(foo, base)
    assert is_more_specific(foo, base)
    assert issubtype(foo, foo)
    assert not (issubtype(base, foo))
    assert not (is_more_specific(foo, foo))
    assert not (issubtype(foo, other))
    assert not (is_more_specific(foo, other))


def test_sort():
    a = Sig(object, object)
    b = Sig(object)
    c = Sig(SuperFoo, object)

    assert is_more_specific(c, a)
    table = SigSet([a, b, c])
    assert list(table) in ([c, b, a], [c, a, b], [b, c, a])


def test_strict_subset():
    a = Sig(SuperFoo, object)
    b = Sig(object, object)
    assert is_more_specific(a, b)
    assert not (is_more_specific(a, a))
    assert not (is_more_specific(b, b))


def test_partial_order_nary():
    # dispatch is check if issubtype(call tuple, target tuple)
    call = Sig(Foo, Foo)
    target = Sig(object, object)
    assert issubtype(call, target)

    call = Sig(Foo, object)
    target = Sig(object, object)
    assert issubtype(call, target)

    call = Sig(Foo, SuperFoo)
    target = Sig(SuperFoo, SuperFoo)
    assert issubtype(call, target)

    call = Sig(Foo, Foo)
    target = Sig(SuperFoo, SuperFoo)
    assert issubtype(call, target)

    call = Sig(Foo, Foo)
    target = Sig(Foo, Foo)
    assert issubtype(call, target)

    # check arity
    call = Sig(Foo,)
    target = Sig(Foo, Foo)
    assert not (issubtype(call, target))


def test_issubtype():

    # strict check
    assert not (issubtype(Foo, Bar))
    assert not (issubtype(Bar, Foo))
    assert issubtype(Foo, Foo)
    assert issubtype(Foo, SuperFoo)
    assert not issubtype(Bar, SuperFoo)
    assert issubtype(Foo, Union[SuperFoo, SuperBar])
    assert issubtype(Bar, Union[SuperFoo, SuperBar])
    assert issubtype(Bar, Union[Foo, Bar])


def test_equality():
    a = Sig(float, str)
    b = Sig(float,)
    assert not a == b


def test_varargs():

    target = Sig(int, int, Vararg)
    assert issubtype(Sig(int, int), target)

    call = Sig(int, int, int)
    assert issubtype(call, target)


def test_poset():
    class Tag:
        pass

    class ATag(Tag):
        pass

    class Node:
        pass

    class ScalarNode(Node):
        pass

    s1 = Sig(Node, Tag)
    s2 = Sig(Node,)
    s3 = Sig(ScalarNode, ATag)
    assert issubtype(s3, s1)
    assert is_more_specific(s3, s1)
    assert not is_more_specific(s2, s1)


def test_type_lit():
    assert issubtype(typing.Type[str], typing.Type[object])
    assert issubtype(typing.Type[str], type)
    assert not issubtype(type, typing.Type[str])
    assert issubtype(typing.Type[Foo], typing.Type[SuperFoo])
    assert not issubtype(typing.Type[Foo], typing.Type[Bar])
