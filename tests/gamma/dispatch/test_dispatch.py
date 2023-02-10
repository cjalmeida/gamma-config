from typing import Any, Dict, Type, Union

import pytest
from gamma.dispatch import DispatchError, dispatch
from gamma.dispatch.dispatchsystem import OverwriteWarning, Sig, methods_matching
from gamma.dispatch.typesystem import Sig, SigSet, Vararg, signatures_from


class SuperFoo:
    pass


class Foo(SuperFoo):
    pass


class SuperBar:
    pass


class Bar(SuperBar):
    pass


def test_simple_dispatch():
    @dispatch
    def temp(a):
        return "fallback"

    @dispatch
    def temp(a: int):
        return "int"

    @dispatch
    def temp(a: float):
        return "float"

    @dispatch
    def temp(a: float, b: str):
        return "float-str"

    assert temp("a") == "fallback"
    assert temp(1) == "int"
    assert temp(1.0) == "float"
    assert temp(1.0, "foo") == "float-str"

    with pytest.raises(DispatchError, match="no method found"):
        temp(1.0, [])


def test_wrong_kwarg_call():
    @dispatch
    def temp(*, c=1):
        return "noarg"

    @dispatch
    def temp(a):
        return "fallback"

    @dispatch
    def temp(a: int):
        return "int"

    assert temp("a") == "fallback"
    assert temp(1) == "int"

    with pytest.raises(DispatchError, match="[Rr]eserved"):
        temp(a=1)

    with pytest.raises(TypeError, match="unexpected keyword"):
        temp(b=1)

    assert temp(c=1) == "noarg"


def test_warn_overwrite():
    @dispatch
    def temp(a):
        return "1 arg"

    with pytest.warns(OverwriteWarning):
        # common mistake to accidentally overwrite a function call
        @dispatch
        def temp(c=1):
            return "overwrites"

    @dispatch(overwrite=True)
    def temp(c=1):
        return "overwrites"

    assert temp(1) == "overwrites"


def test_full_order():
    @dispatch
    def temp(a, b: int):
        return "1"

    @dispatch
    def temp(a: int, b):
        return "2"

    assert temp([], 1) == "1"
    assert temp(1, []) == "2"

    # this is ambiguous
    with pytest.raises(DispatchError):
        temp(1, 1)

    # solve ambiguity
    @dispatch
    def temp(a: int, b: int):
        return "3"

    assert temp(1, 1) == "3"


def test_varargs():
    @dispatch
    def temp(a: int, b: int, *args):
        return f"{a}, {b}"

    assert temp(1, 2) == "1, 2"
    assert temp(1, 2, 3) == "1, 2"
    assert temp(1, 2, 3, 4) == "1, 2"

    with pytest.raises(DispatchError):
        temp(1)

    @dispatch
    def temp(a: int, b: int, c: str, *args):
        return "new"

    assert temp(1, 2, 3) == "1, 2"
    assert temp(1, 2, "3") == "new"


def test_defaults():
    @dispatch
    def temp(a: int, b: int = 1):
        return f"{a}, {b}"

    assert temp(1, 1) == "1, 1"
    assert temp(1, 2) == "1, 2"
    assert temp(1) == "1, 1"


def test_specialization():
    class AbstractFoo:
        pass

    class Foo(AbstractFoo):
        pass

    @dispatch
    def temp(a: AbstractFoo, b: bool):
        return "2 args"

    @dispatch
    def temp(a: Foo):
        return "1 arg"

    assert temp(Foo(), False) == "2 args"
    assert temp(Foo()) == "1 arg"


def test_dispatch_exception():
    @dispatch
    def temp(x: int):  # noqa
        return "int"

    @dispatch
    def temp(x: float):  # noqa
        return "float"

    with pytest.raises(TypeError, match="foo"):
        # invalid number of args, check source file is part of the exception args
        temp(1, foo=1)


def test_name_shadowing():
    # an object with the same name appearing previously in the same namespace
    temp = 123  # noqa

    # a multi-dipatch method shadowing that name
    @dispatch
    def temp(x: int):  # noqa
        return "int"

    @dispatch
    def temp(x: float):
        return "float"

    assert isinstance(temp, dispatch)
    assert temp(0) == "int"
    assert temp(0.0) == "float"


def test_union_sig():
    def temp(x: Union[int, float]):  # noqa
        return "int-float"

    for sig in signatures_from(temp):
        assert "int" in repr(sig)
        assert "float" in repr(sig)


def test_union_call():
    @dispatch
    def temp(x: Union[int, float]):  # noqa
        return "int-float"

    @dispatch
    def temp(x):  # noqa
        return "fallback"

    assert temp(1) == "int-float"
    assert temp(1.0) == "int-float"
    assert temp([]) == "fallback"


def test_inherit_none():
    class Base:
        pass

    class Foo(Base):
        pass

    @dispatch
    def temp(x: Base, y=None):
        return "foo"

    assert temp(Foo()) == "foo"
    assert temp(Foo(), None) == "foo"
    assert temp(Foo(), 1) == "foo"


def test_typing_alias():
    @dispatch
    def temp(x: Dict):
        return "dict"

    @dispatch
    def temp(x):
        return "fallback"

    assert temp(dict(a=1)) == "dict"
    assert temp(1) == "fallback"


def test_cache_reset():
    @dispatch
    def temp(x):
        return "obj"

    assert temp(1) == "obj"

    @dispatch
    def temp(x: int):
        return "int"

    assert temp(1) == "int"


def test_pending():
    # forward reference to types won't work for local classes
    assert global_temp(GlobalFoo()) == "foo"


@dispatch
def global_temp(x: "GlobalFoo"):
    return "foo"


class GlobalFoo:
    pass


def test_manual_setitem():
    @dispatch
    def temp(x: int):
        return "int"

    def alt(*args):
        return "alt"

    temp[str] = alt
    temp[float, float] = alt

    assert temp(1) == "int"
    assert temp("1") == "alt"
    assert temp(1.0, 1.0) == "alt"


def test_specialize1():
    sig1 = Sig(object, object)
    sig2 = Sig(SuperFoo, object)
    sig3 = Sig(Foo, object)
    sig4 = Sig(Foo, SuperFoo)
    sigN = Sig(int, int)
    table = SigSet([sig1, sig2, sig3, sig4, sigN])

    call = Sig(Foo, Foo)
    match = methods_matching(call, table)
    assert match[0] == sig4
    assert sigN not in match
    assert len(match) == 1

    # add an ambiguous match
    # (:Foo, :Foo) matches (:Foo, :SuperFoo) and (:SuperFoo, :Foo)
    # but one is not a strict subtype of the other
    sig5 = Sig(SuperFoo, Foo)
    table.add(sig5)
    match = methods_matching(call, table)
    assert len(match) == 2

    # add a more specific sig
    sig6 = Sig(Foo, Foo)
    table.add(sig6)
    match = methods_matching(call, table)
    assert len(match) == 1


def test_specialize2():
    sig1 = Sig(Foo)
    sig2 = Sig(SuperFoo, bool)
    table = SigSet([sig1, sig2])

    call = Sig(Foo, bool)
    got = methods_matching(call, table)
    assert len(got) == 1
    assert got[0] == sig2

    call = Sig(Foo)
    got = methods_matching(call, table)
    assert len(got) == 1
    assert got[0] == sig1


def test_varargs_dispatch():
    target = Sig(int, int, Vararg)
    call = Sig(int, int, int)
    match = methods_matching(call, [target])
    assert match

    target = Sig(int, int, Vararg)
    call = Sig(int, int)
    match = methods_matching(call, [target])
    assert match


def test_caching():
    @dispatch
    def temp(a):
        return 1

    assert temp("a") == 1

    @dispatch
    def temp(a: str):
        return 2

    assert temp("a") == 2
    assert temp(True) == 1


def test_dispatch_on_types():
    @dispatch
    def temp(a):
        return "fallback"

    @dispatch
    def temp(a: type):
        return "anytype"

    @dispatch
    def temp(a: Type[Bar]):
        return "bar"

    @dispatch
    def temp(a: Type[Foo]):
        return "foo"

    assert temp(1) == "fallback"
    assert temp(Foo) == "foo"
    assert temp(Bar) == "bar"
    assert temp(str) == "anytype"


def test_dispatch_on_any():
    @dispatch
    def temp1(a: Any):
        return "fallback"

    @dispatch
    def temp1(a: int):
        return 1

    #

    @dispatch
    def temp2(a: Any, b: int):
        return "fallback"

    @dispatch
    def temp2(a: int, b: int):
        return 2

    assert temp1(0) == 1
    assert temp1(...) == "fallback"
    assert temp2(0, 0) == 2
    assert temp2(..., 0) == "fallback"
