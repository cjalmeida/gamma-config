from typing import Union
from gamma.dispatch.core import (
    DispatchSignature,
    PODict,
    POSet,
    Vararg,
    issametype,
    issubtype,
    methods_for,
)

DS = DispatchSignature


class SuperFoo:
    pass


class Foo(SuperFoo):
    pass


class SuperBar:
    pass


class Bar(SuperBar):
    pass


def test_partial_order_unary():
    foo = DS((Foo,))
    base = DS((SuperFoo,))
    other = DS((SuperBar,))
    obj = DS((object,))

    assert foo <= obj
    assert foo < base
    assert foo <= base
    assert foo <= foo
    assert not (base < foo)
    assert not (foo < foo)
    assert not (foo < other)
    assert not (foo <= other)


def test_sort():
    a = DS((object, object))
    b = DS((object,))
    c = DS((SuperFoo, object))

    assert c < a
    table = POSet([a, b, c])
    assert list(table) in ([c, b, a], [c, a, b], [b, c, a])


def test_strict_subset():
    a = DS((SuperFoo, object))
    b = DS((object, object))
    assert a < b
    assert not (a < a)
    assert not (b < b)


def test_partial_order_nary():
    # dispatch is check if call tuple <= target tuple
    call = DS((Foo, Foo))
    target = DS((object, object))
    assert call <= target

    call = DS((Foo, object))
    target = DS((object, object))
    assert call <= target

    call = DS((Foo, SuperFoo))
    target = DS((SuperFoo, SuperFoo))
    assert call <= target

    call = DS((Foo, Foo))
    target = DS((SuperFoo, SuperFoo))
    assert call <= target

    call = DS((Foo, Foo))
    target = DS((Foo, Foo))
    assert call <= target

    # check arity
    call = DS((Foo,))
    target = DS((Foo, Foo))
    assert not (call <= target)


def test_podict():
    class PO:
        def __init__(self, val) -> None:
            self.val = val

        def __lt__(self, o) -> bool:
            if type(self.val) is not type(o.val):  # noqa
                return False
            return self.val < o.val

        def __le__(self, o) -> bool:
            if type(self.val) is not type(o.val):  # noqa
                return False
            return self.val <= o.val

        def __eq__(self, o: object) -> bool:
            if type(self.val) is not type(o.val):  # noqa
                return False
            return self.val == o.val

        def __repr__(self) -> str:
            return str(self.val)

    pa = PO("a")
    pb = PO("b")
    p1 = PO(1)
    p2 = PO(2)
    assert pa < pb
    assert p1 < p2
    assert not (pa <= p1) and not (p1 <= pa)

    q = [(pb, 1), (p2, 1), (pa, 1), (p1, 1)]
    podict = PODict(q)
    assert list(podict.keys()) in (
        [pa, pb, p1, p2],
        [p1, p2, pa, pb],
        [p1, pa, p2, pb],
        [pa, p1, p2, pb],
        [pa, p1, pb, p2],
        [p1, pa, pb, p2],
    )


def test_specialize1():

    sig1 = DS((object, object))
    sig2 = DS((SuperFoo, object))
    sig3 = DS((Foo, object))
    sig4 = DS((Foo, SuperFoo))
    sigN = DS((int, int))
    table = POSet([sig1, sig2, sig3, sig4, sigN])

    call = DS((Foo, Foo))
    match = methods_for(call, table)
    assert match[0] == sig4
    assert sigN not in match
    assert len(match) == 1

    # add an ambiguous match
    # (:Foo, :Foo) matches (:Foo, :SuperFoo) and (:SuperFoo, :Foo)
    # but one is not a strict subtype of the other
    sig5 = DS((SuperFoo, Foo))
    table.add(sig5)
    match = methods_for(call, table)
    assert len(match) == 2

    # add a more specific sig
    sig6 = DS((Foo, Foo))
    table.add(sig6)
    match = methods_for(call, table)
    assert len(match) == 1


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


def test_issametype():
    assert issametype(Foo, Foo)
    assert issametype(Foo, Union[Foo, Bar])
    assert issametype(Bar, Union[Foo, Bar])

    assert not issametype(Foo, Bar)
    assert not issametype(Foo, SuperFoo)
    assert not issametype(Foo, Union[SuperFoo, SuperBar])


def test_specialize2():
    sig1 = DS((Foo,))
    sig2 = DS((SuperFoo, bool))
    table = POSet([sig1, sig2])

    call = DS((Foo, bool))
    got = methods_for(call, table)
    assert len(got) == 1
    assert got[0] == sig2

    call = DS((Foo,))
    got = methods_for(call, table)
    assert len(got) == 1
    assert got[0] == sig1


def test_equality():
    a = DS((float, str))
    b = DS((float,))
    assert not a == b


def test_varargs():

    target = DS((int, int, Vararg))
    assert DS((int, int)) <= target

    call = DS((int, int, int))
    assert call <= target

    match = methods_for(call, [target])
    assert match

    target = DS((int, int, Vararg))
    call = DS((int, int))
    match = methods_for(call, [target])
    assert match


def test_poset():
    class Tag:
        pass

    class ATag(Tag):
        pass

    class Node:
        pass

    class ScalarNode(Node):
        pass

    s1 = DS((Node, Tag))
    s2 = DS((Node,))
    s3 = DS((ScalarNode, ATag))
    assert s3 <= s1
    assert s3 < s1
    assert not s2 < s1

    table = POSet([s1, s2, s3])
    call = DS((ScalarNode, ATag))
    match = methods_for(call, table)
    assert len(match) == 1
