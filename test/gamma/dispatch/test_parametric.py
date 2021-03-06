from multimethod import DispatchError
import pytest
from gamma.dispatch import ParametricMeta, parametric, dispatch


class Global(metaclass=ParametricMeta):
    pass


@parametric
class Global2:
    pass


def test_global():
    assert Global.__module__ == __name__
    assert Global["a"].__module__ == __name__

    assert Global2.__module__ == __name__
    assert Global2["a"].__module__ == __name__


def test_parametric_create():
    class Tag(metaclass=ParametricMeta):
        pass

    RefTag1 = Tag["ref"]
    RefTag2 = Tag.of("ref")
    assert RefTag1 is Tag["ref"] is RefTag2

    NamedTag1 = Tag.of("named", name="NamedTag")
    NamedTag2 = Tag["named"]
    NamedTag3 = Tag.of("named", name="NamedTag")
    assert NamedTag1 is NamedTag2 is NamedTag3

    with pytest.raises(NameError):
        Tag.of("named", name="OtherName")

    assert issubclass(RefTag1, Tag)
    assert RefTag1.__values__ == ("ref",)
    assert RefTag1.__module__ == __name__


def test_parametric_deco():
    from typing import NamedTuple

    @parametric
    class Tag:
        pass

    RefTag1 = Tag["ref"]
    RefTag2 = Tag.of("ref")
    assert RefTag1 is Tag["ref"] is RefTag2

    # test interaction with namedtuple
    @parametric
    class FooType(NamedTuple):
        foo: str

    foo1 = FooType["A"]("arg1")
    foo2 = FooType["A"]("arg2")
    foo1a = FooType["A"]("arg1")
    assert foo1.foo == "arg1" and foo2.foo == "arg2"
    assert foo1 == foo1a


def test_parametric_dispatch():

    # create value type hierarchy
    @parametric
    class Tag:
        pass

    RefTag = Tag["ref"]
    FooTag = Tag.of("foo")
    assert RefTag is not FooTag

    # create functions
    @dispatch
    def fun(a):
        return "fallback"

    @dispatch
    def fun(a: Tag):
        return "base"

    @dispatch
    def fun(a: RefTag):
        return "ref"

    @dispatch
    def fun(a: Tag["foo"]):  # noqa: F821
        return "foo"

    assert fun(1) == "fallback"
    assert fun(Tag["new"]()) == "base"
    assert fun(RefTag()) == "ref"
    assert fun(FooTag()) == "foo"

    @dispatch
    def bar(a: RefTag):
        return "ok"

    assert bar(RefTag()) == "ok"

    with pytest.raises(DispatchError):
        bar(RefTag)


def test_also_of():
    from gamma.dispatch import parametric

    # create value type hierarchy
    @parametric
    class Tag:
        pass

    ATag = Tag["A"]
    BTag = ATag.also_of("B")
    assert ATag is BTag
    assert Tag["A"] is Tag["B"]


def test_union():
    from gamma.dispatch import parametric, dispatch
    from typing import Union

    @parametric
    class Tag:
        pass

    ATag = Tag["A"]
    BTag = Tag["B"]
    AorB = Union[ATag, BTag]

    @dispatch
    def fun(a):
        return "fail"

    @dispatch
    def fun(a: AorB):
        return "ok"

    assert fun(ATag()) == "ok"
    assert fun(BTag()) == "ok"
    assert fun(Tag["C"]()) == "fail"
