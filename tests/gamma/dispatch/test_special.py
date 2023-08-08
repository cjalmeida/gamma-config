import pytest

from gamma.dispatch import dispatch as base_dispatch
from gamma.dispatch.dispatchsystem import DispatchError

dispatch = base_dispatch(namespace="myns")
specialize = base_dispatch(namespace="myns", specialize=True)


def _create_foo_1():
    @dispatch
    def foo(a: int):
        return "int"

    return foo


def _create_foo_2():
    @dispatch
    def foo(a: str):
        return "str"

    return foo


def test_namespaced_and_special():

    # specialize should not work here
    with pytest.raises(DispatchError):

        @specialize
        def foo(a):
            return "obj"

    # create out of scope functions
    _create_foo_1()
    _create_foo_2()

    # create a third binding function
    @specialize
    def foo(a: float):
        return "float"

    assert foo(1) == "int"
    assert foo("a") == "str"
    assert foo(1.0) == "float"
