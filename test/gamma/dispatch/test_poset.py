import pytest
from gamma.dispatch.poset import PODict, POSet


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


def test_podict():

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

    del podict[pb]
    assert list(podict.keys()) in ([pa, p1, p2], [p1, p2, pa], [p1, pa, p2])

    podict[pa] = 100
    assert list(podict.keys()) in ([pa, p1, p2], [p1, p2, pa], [p1, pa, p2])
    assert podict[pa] == 100

    with pytest.raises(KeyError):
        podict[pb]

    podict[pb] = 200
    got = podict.pop(pb)
    assert got == 200
    assert list(podict.keys()) in ([pa, p1, p2], [p1, p2, pa], [p1, pa, p2])

    with pytest.raises(KeyError):
        podict.pop(pb)
    assert 1 == podict.pop(pb, 1)

    assert list(podict) == list(podict.keys())
    assert list(x[0] for x in podict.items()) == list(podict)
    assert list(x[1] for x in podict.items()) == list(podict.values())
    assert pa in podict

    podict.clear()
    assert len(podict) == 0


    poset = POSet([pb, p1, pa, p2])
    assert list(poset) in (
        [pa, pb, p1, p2],
        [p1, p2, pa, pb],
        [p1, pa, p2, pb],
        [pa, p1, p2, pb],
        [pa, p1, pb, p2],
        [p1, pa, pb, p2],
    )
    poset.remove(pa)
    poset.remove(pb)
    assert list(poset) == [p1, p2]

    poset.add(pa)
    assert list(poset) in ([pa, p1, p2], [p1, p2, pa], [p1, pa, p2])
