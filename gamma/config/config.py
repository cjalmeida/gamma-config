import copy
import inspect
import logging
import os
import threading
import weakref
from abc import ABC, abstractproperty
from collections import UserDict
from pathlib import Path, WindowsPath
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Set

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedBase

from . import yaml_merge, subprocess
from . import tags as tags_module

blacklist: Set[str] = set()

logger = logging.getLogger(__name__)


class Config(UserDict):
    """Represents a configuration value, potentially returned from resolving a tag.

    Args:
        data: The underlying data to render

    Keyword Args:
        parent: The parent Value in the configuration tree that originated this.
            Should be None for the root value.
    """

    def __init__(
        self,
        data,
        *,
        parent: Optional["Config"] = None,
        _tags: Dict[str, Callable] = None,
    ):
        super().__init__()
        self.data = data
        self.parent = parent
        self._tags: Optional[Dict[str, Callable]] = _tags

        if self.parent:
            self._dump_mode = None
        else:
            self._dump_mode = False

            # load tags
            if self._tags is None:
                self._tags = tags_module.get_tags()
                # we get raw_value from self.data

        self._stack = [(data, data)]
        self._allow_dot_access = True

    @property
    def _root(self):
        """Pointer to the root config in the tree."""
        if self.parent is None:
            return self
        return self.parent._root

    @property
    def tags(self) -> Dict[str, Callable]:
        if self._tags is None and self.parent is not None:
            return self.parent.tags
        if self._tags is None:
            raise ValueError("tags not initialized")
        return self._tags

    @property
    def dump_mode(self):
        """The dump mode. If None, get from parent"""
        if self._dump_mode is None:
            return self.parent.dump_mode
        return self._dump_mode

    @dump_mode.setter
    def dump_mode(self, value):
        self._dump_mode = value

    def push(self, partial: Mapping):
        """Push and merge a partial config dict into the configuration stack"""
        self._check_root()
        self._merge_data(partial)
        self._stack.insert(0, (partial, self.data))

    def pop(self):
        """Pop the last pushed partial, reverting the config state"""
        self._check_root()
        self._stack.pop()
        _, self.data = self._stack[0]

    def _merge_data(self, partial: Mapping):
        """Merge a partial with the current state"""
        yaml_merge.merge(self.data, partial)

    def __getitem__(self, key):
        val = self.data[key]
        return Renderer(config=self, dump=self.dump_mode, tags=self.tags).render(val)

    def __getattr__(self, key):
        if key.startswith("_") or not self._allow_dot_access or self.dump_mode:
            return object.__getattribute__(self, key)

        if key not in self.data:
            return Config({}, parent=self)

        return self[key]

    def _check_root(self):
        """Check if we're the root config object"""
        if self.parent is not None:
            raise Exception(
                "Config stack push/pull only implemented for the root config object"
            )

    def to_json(self, *, sort=False, **kwargs) -> str:
        """Dumps the config object to YAML string

        Keyword args are passed to the ``json.dumps`` function

        Keyword Args:
            sort: If True, will sort the keys before returning
        """
        import json

        new = self.to_dict(sort=sort)
        return json.dumps(new, **kwargs)

    def to_yaml(self, *, resolve_tags=True) -> str:
        """Dumps the config object to YAML string

        Keyword Args:
            resolve_tags: If True (default), will dump the rendered result of the
                custom tags at the time of the call. Otherwise, will keep the original
                tags.
        """

        from ruamel.yaml import YAML
        import io

        yaml = YAML(typ="rt")
        yaml.representer.add_representer(Config, Config._yaml_representer)

        stream = io.StringIO()
        if resolve_tags:
            self.dump_mode = True
            yaml.dump(self, stream)
            self.dump_mode = False
        else:
            yaml.dump(self.data, stream)

        return stream.getvalue()

    def to_dict(self: Any, sort=False, _first=True) -> Any:
        """Dumps the resolved config object to a Python dict recursively

        Args:
            sort: If True, will sort by keys before returning
        """
        return Renderer(config=self, dump=True, tags=self.tags, sort=sort).render(
            self.data
        )

    def __deepcopy__(self, memo):
        new = Config({})
        new.__dict__.update(self.__dict__)

        if self.dump_mode:
            for k, v in self.items():
                new.data[k] = copy.deepcopy(v, memo)
        else:
            new.data = copy.deepcopy(self.data, memo)
        return new

    @staticmethod
    def _yaml_representer(dumper, data):
        return dumper.represent_dict(data)


class RenderContext:
    def __init__(self, value, **kwargs):
        self.value = value
        self.kwargs = kwargs


class Renderer:
    def __init__(
        self,
        config: Config = None,
        dump: bool = None,
        tags=None,
        render_tags=True,
        render_recurse=True,
        sort=False,
    ):
        self.tags = tags
        self.config = config
        self.dump = dump
        self.render_tags = render_tags
        self.render_recurse = render_recurse
        self.sort = sort

    def render(self, val):
        """Render the data.

        Return:
            Any of a sub-config, a scalar, a list, handling tags as needed.
        """
        if (
            self.render_tags
            and isinstance(val, CommentedBase)
            and hasattr(val, "tag")
            and val.tag.value is not None
        ):
            return self.render_tag(val)

        # return tags as is if we're in dump mode
        if (
            self.dump
            and isinstance(val, CommentedBase)
            and hasattr(val, "tag")
            and val.tag.value is not None
        ):
            return val

        # sub mapping as config for lazy rendering
        if isinstance(val, Mapping) and not self.dump:
            sub = Config(val, parent=self.config)
            return sub

        # dump returns plain dict and render recursively
        if isinstance(val, Mapping) and self.dump:

            if not self.render_recurse:
                return val

            sub = {}
            keys = list(val.keys())
            if self.sort:
                keys.sort()
            for k in keys:
                sub[k] = self.render(val[k])
            return sub

        if isinstance(val, (str, bytes)):
            return val

        if isinstance(val, Iterable):
            if not self.render_recurse:
                return val

            # don't sort arrays as order matters
            res = [self.render(x) for x in val]
            return res

        # anything else, return as is
        return val

    def render_tag(self, node):
        """Proces tagged nodes"""

        tag = node.tag.value
        try:
            func = self.tags[tag]
        except KeyError:
            raise KeyError(f"Handler function for tag {tag} was not found.")

        argspec = inspect.getfullargspec(func)
        func_args = set(argspec.args) | set(argspec.kwonlyargs)
        args = {}
        if "root" in func_args:
            args["root"] = self.config._root
        if "value" in func_args:
            args["value"] = node.value
        if "tag" in func_args:
            args["tag"] = tag
        if "dump" in func_args:
            args["dump"] = self.dump
        if "node" in func_args:
            args["node"] = node

        val = func(**args)
        renderer = copy.copy(self)
        renderer.render_tags = False  # force to avoid infinite loops

        if isinstance(val, RenderContext):
            renderer.__dict__.update(val.kwargs)
            val = val.value

        return renderer.render(val)


class ConfigLoader(ABC):
    """Abstract class implementing a Config loader."""

    def __init__(self, yaml: YAML):
        self.yaml = yaml
        self.is_windows_path = isinstance(Path(), WindowsPath)

    @abstractproperty
    def entries(self) -> List[str]:
        """List of URIs mapping to YAML config files.

        Each entry is loaded in order and merged into the config
        """

    def load(self, config: Config):
        """Load YAML config entries into a Config object.
        """

        def _sort_key(el: str):
            splits = el.rsplit("/", 1)
            return splits[0] if len(splits) == 1 else splits[1]

        entries = sorted(self.entries, key=_sort_key)
        for entry in entries:
            content = self.get_content(entry)
            if not content.strip():
                logger.warning(f"Entry '{entry}' is empty. Skipping")
            data = self.yaml.load(content)
            config.push(data)

        return config

    def get_content(self, entry: str) -> str:
        """The the content for a single entry URI.

        By default, it supports handling only standard ``file://`` URIs. Extensions
        may add support for other protocols

        Args:
            entry: An entry URI, in whatever format returned by the ``entries`` method.
        """
        from urllib.parse import urlsplit, unquote_plus
        from pathlib import Path

        url = urlsplit(entry)

        if not url.scheme == "file":
            raise Exception(f"Can't understand scheme '{url.scheme}' for URI '{entry}")

        path = unquote_plus(url.path)
        if self.is_windows_path:
            path = path.lstrip("/")
        return Path(path).read_text()


class MetaConfigLoader(ConfigLoader):
    """A ConfigLoader for the meta config object"""

    @property
    def entries(self) -> List[str]:
        home = get_config_root()
        meta: Path = home / "00-meta.yaml"
        return [meta.as_uri()]

    def load_plugins(self, meta) -> None:
        import importlib

        for modname in meta.get("plugins", {}).get("modules", []):
            importlib.import_module(modname)


class DefaultConfigLoader(ConfigLoader):
    """A ConfigLoader for the ``config/`` folder, supporting environments"""

    @property
    def entries(self) -> List[str]:
        from pathlib import Path

        cfg_dir = get_config_root()

        # default
        files: List[Path] = list(cfg_dir.glob("*.yaml"))
        files += list(cfg_dir.glob("*.yml"))

        # environment
        meta = get_meta_config()
        for entry in meta.get("include_folders", []):
            include_dir = cfg_dir / entry

            if include_dir.exists():
                files += list(include_dir.glob("*.yaml"))
                files += list(include_dir.glob("*.yml"))

        # use the file name as sort key, regardless of folder
        files.sort(key=lambda f: f.name)
        files_str = [str(f.absolute().as_uri()) for f in files]

        return files_str


class LocalStore:
    def __init__(self):
        self.__dict__["__threadstore"] = {}

    def __get_store(self):
        store: dict = object.__getattribute__(self, "__threadstore")
        key = (os.getpid(), threading.get_ident())
        if key not in store:
            store[key] = {}

            def _remove():
                del store[key]

            weakref.finalize(threading.current_thread(), _remove)

        return store[key]

    def __getattribute__(self, name):
        if not name.startswith("__"):
            try:
                return object.__getattribute__(self, "_LocalStore__get_store")()[name]
            except KeyError:
                raise AttributeError(name)

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if not name.startswith("__"):
            store = object.__getattribute__(self, "_LocalStore__get_store")()
            store[name] = value
        else:
            self.__dict__[name] = value

    def __delattr__(self, name):
        try:
            if not name.startswith("__"):
                store = object.__getattribute__(self, "_LocalStore__get_store")()
                del store[name]
            else:
                del self.__dict__[name]
        except KeyError:
            raise AttributeError(name)


_config_store = LocalStore()


def load_dotenv(root: Path = None):
    """Load dotenv files located in:

        {config_root}/../config.local.env
        {config_root}/../config.env
    """

    import dotenv

    if root is None:
        get_config_root()
    else:
        home = root.parent
        dotenv.load_dotenv(f"{home}/config.local.env")
        dotenv.load_dotenv(f"{home}/config.env")


def get_config_root() -> Path:
    """Return the location for config root path.

    Overridable with the GAMMA_CONFIG_ROOT environment variable.

    This can be used in scripts or tests to change the expected location of the
    project home without changing the current working folder.
    """

    root: Optional[Path] = Path(
        os.getenv("GAMMA_CONFIG_ROOT", Path("config").absolute())
    )

    if not root or not (root / "00-meta.yaml").exists():
        root = _try_jupyter_config_root()

    if root is None:
        raise Exception("Cannot locate a gamma config root in any expected location.")

    load_dotenv(root)
    return root


def _try_jupyter_config_root() -> Optional[Path]:
    """Try to find a ``config/00-meta.yaml`` file under current directory parents
    if we detect we're operating inside Jupyter."""

    if not _isnotebook():
        return None

    path = Path(".").absolute()
    while path != path.parent:
        candidate = path / "config"
        if (candidate / "00-meta.yaml").exists():
            return candidate
        path = path.parent

    return None


def _isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return True  # Terminal running IPython
        else:
            return True  # Other type of IPython kernel (?)
    except NameError:
        return False  # Probably standard Python interpreter


def set_config_root(path: str) -> None:
    """Shortcut to set the GAMMA_CONFIG_ROOT env variable.

    Do not use in tests, prefer ``monkeypatch.setenv``
    """
    os.environ["GAMMA_CONFIG_ROOT"] = path


def reset_config() -> None:
    if hasattr(_config_store, "meta"):
        del _config_store.meta
    if hasattr(_config_store, "config"):
        del _config_store.config
    if hasattr(_config_store, "tags"):
        del _config_store.tags


def get_config() -> Config:
    if not hasattr(_config_store, "config"):
        # try serialized config
        if subprocess.ENV_KEY in os.environ:
            _config_store.config = subprocess.deserialize()
        else:
            from . import tags

            yaml = YAML(typ="rt")
            _config = Config({}, _tags=tags.get_tags(blacklist=True))
            DefaultConfigLoader(yaml=yaml).load(_config)
            _config_store.config = _config
    return _config_store.config


def create_config_from_string(yaml_str: str) -> "Config":
    """Simple Config factory that builds a config object from a YAML string"""

    yaml = YAML(typ="rt")
    _config = Config({}, _tags=tags_module.get_tags(blacklist=True))
    content = yaml.load(yaml_str)
    _config.push(content)
    return _config


def get_meta_config() -> "Config":
    if not hasattr(_config_store, "meta") is None:
        yaml = YAML(typ="rt")
        _config_store.meta = Config({}, _tags=tags_module.get_tags(blacklist=False))
        loader = MetaConfigLoader(yaml=yaml)
        loader.load(_config_store.meta)

        # reset tags to ensure extra modules are available
        tags_module.reset_tags()
        loader.load_plugins(_config_store.meta)

    return _config_store.meta
