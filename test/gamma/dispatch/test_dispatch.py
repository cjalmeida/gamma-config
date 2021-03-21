from gamma.dispatch import dispatch


def test_kwargs():
    @dispatch
    def temp(a: int, b: int):
        return f"{a}, {b}"

    @dispatch
    def temp(a: int):
        return temp(a, 1)

    assert temp(1, 2) == "1, 2"
    assert temp(1) == "1, 1"

    # TODO: this is currently not working
    # assert temp(1, b=3) == "1, 3"


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

    # TODO: bug in dispatch, should match Julia behavior here
    assert temp(Foo(), False) == "2 args"
    assert temp(Foo()) == "1 arg"
