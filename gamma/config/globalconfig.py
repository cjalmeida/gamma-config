import multiprocessing
import threading

from .confignode import RootConfig, push_entry
from .findconfig import get_entries
from .load import load_node


class _GlobalStore:
    def __init__(self) -> None:
        self.root = None
        self.load_key = None
        self.load_thread_name = None
        self.load_pid = None

    def set(self, root, force=False):
        """Set the new root config.

        To avoid unwanted suprises, by defaul we allow updating the global root config
        only by the same thread that created it.

        Args:
            root: the RootConfig to store
            force: if True, do not check for thread safety
        """

        thread = threading.current_thread()
        pid = multiprocessing.current_process().pid
        key = (thread.ident, pid)
        if force or self.root is None or self.load_key == key:
            self.root = root
            self.load_key = key
            self.load_thread_name = threading.current_thread().name
            return

        raise Exception(
            f"Current thread {thread.name}(tid={key[0]}; pid={key[1]}) tried to update "
            f"the global config that was originally loaded from thread "
            f"{self.load_thread_name}(tid={self.load_key[0]}; pid={self.load_key[1]})"
        )

    def get(self) -> RootConfig:
        return self.root

    def empty(self) -> bool:
        return self.root is None


_global_store = _GlobalStore()


def get_config():
    if _global_store.empty():
        entries = sorted(get_entries())
        root = RootConfig()
        for entry_key, entry in entries:
            node = load_node(entry)
            if node:
                push_entry(root, entry_key, node)

        _global_store.set(root)
    return _global_store.get()


def reset_config():
    global _global_store
    _global_store = _GlobalStore()
