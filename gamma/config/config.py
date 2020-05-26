import inspect
import os
from abc import ABC, abstractproperty
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Type,
    Any,
)
import copy
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedBase
import threading
from collections import UserDict
from . import dict_merge, tags as tags_module, subprocess

blacklist: Set[str] = set()


class EnvironmentFolderException(Exception):
    def __init__(self, folder, **kwargs):
        super().__init__(f"Environment folder '{folder}' not found.", **kwargs)


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
        dict_merge.merge(self.data, partial)

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

    @abstractproperty
    def entries(self) -> List[str]:
        """List of URIs mapping to YAML config files.

        Each entry is loaded in order and merged into the config
        """

    def load(self, config: Config):
        """Load YAML config entries into a Config object.
        """

        entries = sorted(self.entries, key=lambda x: x[0])
        for entry in entries:
            content = self.get_content(entry)
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
        from urllib.parse import urlsplit, unquote
        from pathlib import Path

        url = urlsplit(entry)

        if not url.scheme == "file":
            raise Exception(f"Can't understand scheme '{url.scheme}' for URI '{entry}")

        return Path(unquote(url.path)).read_text()


class MetaConfigLoader(ConfigLoader):
    """A ConfigLoader for the meta config object"""

    @property
    def entries(self) -> List[str]:
        home = get_project_home()
        return [f"file://{home}/config/00-meta.yaml"]


class DefaultConfigLoader(ConfigLoader):
    """A ConfigLoader for the ``config/`` folder, supporting environments"""

    @property
    def entries(self) -> List[str]:
        from pathlib import Path

        cfg_dir = Path(get_project_home()) / "config"

        # default
        files: List[Path] = list(cfg_dir.glob("*.yaml"))
        files += list(cfg_dir.glob("*.yml"))

        # environment
        meta = get_meta_config()
        environment = meta["environment"]
        env_dir = cfg_dir / environment

        if env_dir.exists():
            files += list(env_dir.glob("*.yaml"))
            files += list(env_dir.glob("*.yml"))
        else:
            raise EnvironmentFolderException(env_dir)

        # use the file name as sort key, regardless of folder
        files.sort(key=lambda f: f.name)
        files_str = [str(f.absolute().as_uri()) for f in files]
        return files_str


class LocalStore(threading.local):
    def __init__(self):
        self.__dict__["__pid"] = os.getpid()

    def __getattribute__(self, name):
        if not name.startswith("__"):
            object.__getattribute__(self, "__check_pid__")()
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if not name.startswith("__"):
            object.__getattribute__(self, "__check_pid__")()
        self.__dict__[name] = value

    def __delattr__(self, name):
        if not name.startswith("__"):
            object.__getattribute__(self, "__check_pid__")()
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name)

    def __check_pid__(self):
        d = self.__dict__

        if d["__pid"] != os.getpid():
            d.clear()
            d["__pid"] = os.getpid()


_config_store = LocalStore()


def get_project_home() -> str:
    """Return the location for project home.

    Overridable with the PROJECT_HOME environment variable.

    This can be used in scripts or tests to change the expected location of the
    project home without changing cwd.
    """
    return os.getenv("PROJECT_HOME", os.path.abspath(os.path.dirname(os.curdir)))


def reset_config() -> None:
    if hasattr(_config_store, "meta"):
        del _config_store.meta
    if hasattr(_config_store, "config"):
        del _config_store.config


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
        MetaConfigLoader(yaml=yaml).load(_config_store.meta)
    return _config_store.meta
