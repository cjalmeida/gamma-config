"""Module dealing with the lifecycle of the global `RootConfig` object"""

import multiprocessing
import threading
from typing import Optional, Tuple

from .cache import cache
from .confignode import RootConfig, push_entry
from .findconfig import get_entries
from .load import load_node


class _GlobalStore:
    """Implements a global store holder object.

    This store operates as a restricted version of a thread-local, where you can only
    ovewrite the value in the same thread/processes where it was first set.
    """

    def __init__(self) -> None:
        self.root = None
        self.load_key = None
        self.load_thread_name = None
        self.load_pid = None

    def set(self, root, force=False) -> None:
        """Set the new root config.

        To avoid unwanted suprises, by defaul we allow updating the global root config
        only by the same thread that created it.

        Args:
            root: the RootConfig to store
            force: if True, do not check for thread safety
        """

        key = self._get_load_key()
        if not force:
            self.check_can_modify(key=key)

        self.root = root
        self.load_key = key
        self.load_thread_name = threading.current_thread().name

    def get(self) -> RootConfig:
        return self.root

    def empty(self) -> bool:
        return self.root is None

    def reset(self, force=False) -> None:
        if not force:
            self.check_can_modify()
        self.__init__()

    def _get_load_key(self) -> Tuple[int, int]:
        thread = threading.current_thread()
        pid = multiprocessing.current_process().pid
        key = (thread.ident, pid)
        return key

    def check_can_modify(self, key=None) -> None:
        """Raises an Exception modifying the config would break the same thread rule.

        Args:
            key: the key to check, fetches one if `None`
        """
        key = key or self._get_load_key()
        if self.root is None or self.load_key == key:
            return

        thread = threading.current_thread()
        raise Exception(
            f"Current thread {thread.name}(tid={key[0]}; pid={key[1]}) tried to update "
            f"the global config that was originally loaded from thread "
            f"{self.load_thread_name}(tid={self.load_key[0]}; pid={self.load_key[1]})"
        )


_global_store = _GlobalStore()


def get_config(initialize: bool = True) -> Optional[RootConfig]:
    """Get the global config root object, loading if needed and `initialize` is `True`.

    This global object is cached and safe to call multiple times, from multiple
    threads.
    """
    if _global_store.empty() and not initialize:
        return None
    elif _global_store.empty() and initialize:
        entries = sorted(get_entries())
        root = RootConfig()
        for entry_key, entry in entries:
            node = load_node(entry)
            if node:
                push_entry(root, entry_key, node)

        _global_store.set(root)
    return _global_store.get()


def reset_config(force: bool = False) -> None:
    """Clear the global store and cache.

    This is not meant to be used extensively by applications, but can be useful for
    writing tests.

    Args:
        force: if True, will reset the global store regardless of the current
            thread/process.
    """

    _global_store.reset(force=force)
    cache.clear()


def set_config(cfg: RootConfig) -> None:
    """Forces a root config.

    Call `reset_config`.

    NOTE: This is not meant to be used regularly by applications, but can be useful
    when writing tests.
    """
    reset_config()
    _global_store.set(cfg)


def check_can_modify(cfg: RootConfig) -> None:
    """Check if this root config object can be modified.

    As specified, the **global** root config object can only be modified by the thread
    that first created it.
    """

    if _global_store.root is cfg:
        _global_store.check_can_modify()
