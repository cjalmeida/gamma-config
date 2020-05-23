import inspect
import os
from abc import ABC, abstractproperty
from collections import UserDict
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set
import copy
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedBase
import threading

from . import dict_merge, tags, subprocess

blacklist: Set[str] = set()


class EnvironmentFolderException(Exception):
    def __init__(self, folder, **kwargs):
        super().__init__(f"Environment folder '{folder}' not found.", **kwargs)


class Config(UserDict):
    """The main config object.

    Act as a regular dict, with functionality to render custom tags.

    Args:
        data: The raw content.
        parent: The parent Config object, for sub entries.
        tags: The dict of (str, callable) with tag handlers.
    """

    def __init__(
        self,
        data: Mapping = None,
        parent: "Config" = None,
        tags: Dict[str, Callable] = None,
    ):
        data = data or {}
        super().__init__(data)

        self._parent = parent
        self._dump_mode = False

        if tags:
            self.tags = tags
        else:
            self.tags = parent.tags

        # Holds a stack of config dicts (partial, rendered). The stack[0][1] entry
        # should always match self.data
        self._stack = [(data, data)]

        self._allow_dot_access = True

    @property
    def _root(self):
        """Pointer to the root config object."""

        if self._parent is None:
            return self
        return self._parent._root

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
        return self._parse_value(val)

    def __getattr__(self, key):

        if key.startswith("_") or not self._allow_dot_access or self._dump_mode:
            return object.__getattribute__(self, key)

        if key not in self.data:
            return self._parse_value({})

        return self[key]

    def _check_root(self):
        """Check if we're the root config object"""
        if self._parent is not None:
            raise Exception(
                "Config stack push/pull only implemented for the root config object"
            )

    def _parse_value(self, val):
        """Parse a config entry value.

        Return:
            Any of a sub-config object, a scalar, a list, handling tags as needed.
        """

        if (
            isinstance(val, CommentedBase)
            and hasattr(val, "tag")
            and val.tag.value is not None
        ):
            val = self._process_tagged(val)

        if isinstance(val, Mapping):
            sub = Config(val, self)
            sub._dump_mode = self._dump_mode
            return sub

        if isinstance(val, (str, bytes)):
            return val

        if isinstance(val, Iterable):
            return [self._parse_value(x) for x in val]

        # anything else, return as is
        return val

    def _process_tagged(self, node):
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
            args["root"] = self._root
        if "value" in func_args:
            args["value"] = node.value
        if "tag" in func_args:
            args["tag"] = tag
        if "dump" in func_args:
            args["dump"] = self._dump_mode
        if "node" in func_args:
            args["node"] = node

        return func(**args)

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
            self._dump_mode = True
            yaml.dump(self, stream)
            self._dump_mode = False
        else:
            yaml.dump(self.data, stream)

        return stream.getvalue()

    def to_dict(self) -> Dict:
        """Dumps the config object to a Python dict recursively
        """

        new = {}
        self._dump_mode = True
        for k, v in self.items():
            if isinstance(v, Config):
                v = v.to_dict()
            new[k] = v
        self._dump_mode = False

        return new

    def dump(self, *, resolve_tags=True) -> "Config":

        if resolve_tags:
            self._dump_mode = True
            new = copy.deepcopy(self)
            self._dump_mode = False
            new._dump_mode = False
            return new
        else:
            return copy.deepcopy(self)

    def __deepcopy__(self, memo):
        new = Config({}, parent=self._parent, tags=self.tags)
        new._dump_mode = self._dump_mode

        if self._dump_mode:
            for k, v in self.items():
                new.data[k] = copy.deepcopy(v, memo)
        else:
            new.data = copy.deepcopy(self.data, memo)
        return new

    @staticmethod
    def _yaml_representer(dumper, data):
        return dumper.represent_dict(data)


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
        return {f"file://{home}/config/00-meta.yaml"}


class DefaultConfigLoader(ConfigLoader):
    """A ConfigLoader for the ``config/`` folder, supporting environments"""

    @property
    def entries(self) -> List[str]:
        from pathlib import Path

        cfg_dir = Path(get_project_home()) / "config"

        # default
        files: List[Path] = list(cfg_dir.glob(f"*.yaml"))
        files += list(cfg_dir.glob(f"*.yml"))

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
        files = [str(f.absolute().as_uri()) for f in files]
        return files


_config_store = threading.local()


def get_project_home():
    """Return the location for project home.

    Overridable with the PROJECT_HOME environment variable.

    This can be used in scripts or tests to change the expected location of the
    project home without changing cwd.
    """
    return os.getenv("PROJECT_HOME", os.path.abspath(os.path.dirname(os.curdir)))


def reset_config() -> Config:
    del _config_store.config


def get_config() -> Config:
    if not hasattr(_config_store, "config") is None:
        # try serialized config
        if subprocess.ENV_KEY in os.environ:
            _config_store.config = subprocess.deserialize()
        else:
            from . import tags

            yaml = YAML(typ="rt")
            _config = Config(tags=tags.get_tags(blacklist=True))
            DefaultConfigLoader(yaml=yaml).load(_config)
            _config_store.config = _config
    return _config_store.config


def create_config_from_string(yaml_str: str) -> "Config":
    """Simple Config factory that builds a config object from a YAML string"""

    yaml = YAML(typ="rt")
    _config = Config(tags=tags.get_tags(blacklist=True))
    content = yaml.load(yaml_str)
    _config.push(content)
    return _config


def get_meta_config() -> "Config":
    if not hasattr(_config_store, "meta") is None:
        yaml = YAML(typ="rt")
        _config_store.meta = Config(tags=tags.get_tags(blacklist=False))
        MetaConfigLoader(yaml=yaml).load(_config_store.meta)
    return _config_store.meta
