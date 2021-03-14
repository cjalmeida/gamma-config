"""Module declaring a cache utility for gamma.config"""

from typing import Any, Mapping


class Cache(Mapping):
    """
    A cache backed by a in-memory `dict`
    """

    def __init__(self) -> None:
        self.store = dict()

    def __getitem__(self, key) -> Any:
        return self.store.__getitem__(key)

    def __iter__(self):  # pragma: no cover
        return self.store.__iter__()

    def __setitem__(self, key, value):
        return self.store.__setitem__(key, value)

    def __len__(self) -> int:  # pragma: no cover
        return self.store.__len__()

    def clear(self):
        """Clear cache contents"""
        return self.store.clear()


cache = Cache()
