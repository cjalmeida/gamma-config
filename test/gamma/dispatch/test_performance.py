from timeit import default_timer as timer

from gamma.dispatch import dispatch


class Base:
    def __call__(self, *args, **kwargs):
        return "fallback"


def test_simple_dispatch():
    @dispatch
    def temp(a):
        return "fallback"

    @dispatch
    def temp(a: int):
        return "int"

    base = Base()

    # warm
    base(1)
    temp(1)

    n = 100_000
    start = timer()
    for _ in range(n):
        base(1)
    base_t = timer() - start

    start = timer()
    for _ in range(n):
        temp(1)
    test_t1 = timer() - start

    print(base_t)
    print(test_t1)
    print(test_t1 / base_t)
    assert test_t1 / base_t < 16


def test_kwargs():
    @dispatch
    def temp(a, *, c=1):
        return "fallback"

    @dispatch
    def temp(a: int, *, c=1):
        return "int"

    base = Base()

    # warm
    base(1, c=2)
    temp(1, c=2)

    n = 100_000
    start = timer()
    for _ in range(n):
        base(1, c=2)
    base_t = timer() - start

    start = timer()
    for _ in range(n):
        temp(1, c=2)
    test_t1 = timer() - start

    print(base_t)
    print(test_t1)
    print(test_t1 / base_t)
    assert test_t1 / base_t < 10
