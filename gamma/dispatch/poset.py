from collections.abc import MutableMapping, MutableSet
from operator import __eq__, __lt__
from typing import Generic, Iterable, List, Tuple, TypeVar

KT = TypeVar("KT")
VT = TypeVar("VT")


class PODict(MutableMapping, Generic[KT, VT]):
    """Dictionary that stores keys sorted (like a prio queue) that works
    for partial orders"""

    data: List[Tuple[KT, VT]]
    __unset = object()

    def __init__(self, data=None, lt=__lt__, eq=__eq__) -> None:
        self.data = []
        self.el_lt = lt
        self.el_eq = eq
        if data:
            # initialize
            items = getattr(data, "items", lambda: data)
            for k, v in items():
                self[k] = v

    def __setitem__(self, key: KT, value: VT) -> None:
        for i, (k, _) in enumerate(self.data):
            if self.el_eq(key, k):
                self.data.pop(i)
                self.data.insert(i, (key, value))
                return
            elif self.el_lt(key, k):
                self.data.insert(i, (key, value))
                return
        self.data.append((key, value))

    def __getitem__(self, key: KT) -> VT:
        for (k, v) in self.data:
            if self.el_eq(key, k):
                return v
        raise KeyError(key)

    def pop(self, key: KT, default=__unset) -> VT:
        try:
            item = self.popitem(key)
        except KeyError:
            if default is self.__unset:
                raise
            return default
        else:
            return item[1]

    def popitem(self, key: KT, default=__unset) -> Tuple[KT, VT]:
        for i, (k, v) in enumerate(self.data):
            if self.el_eq(key, k):
                self.data.pop(i)
                return k, v

        if default is not self.__unset:
            return default
        raise KeyError(key)

    def __iter__(self):
        return self.keys()

    def __len__(self) -> int:
        return self.data.__len__()

    def __delitem__(self, key: KT) -> None:
        for i, (k, _) in enumerate(self.data):
            if key == k:
                self.data.pop(i)
                return

    def keys(self) -> Iterable[KT]:
        return (x[0] for x in self.data)

    def items(self) -> Iterable[KT]:
        return iter(self.data)

    def values(self) -> Iterable[VT]:
        return (x[1] for x in self.data)

    def __contains__(self, o) -> bool:
        return o in self.keys()

    def clear(self) -> None:
        return self.data.clear()


class POSet(PODict[KT, None], MutableSet, Generic[KT]):
    def __init__(self, data, lt=__lt__, eq=__eq__) -> None:
        d = []
        for k in data:
            d.append((k, None))
        super().__init__(d, lt, eq)

    def add(self, value) -> None:
        self[value] = None

    def discard(self, value) -> None:
        del self[value]
