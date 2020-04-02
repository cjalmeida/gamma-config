import inspect
import os
from abc import ABC, abstractproperty
from collections import UserDict
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import fsspec
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedBase

from . import dict_merge, tags

PROJECT_HOME = os.getenv("PROJECT_HOME", os.path.abspath(os.path.dirname(os.curdir)))
PROJECT_HOME = f"file://{PROJECT_HOME}"

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

        self.parent = parent
        self._dump_mode = False

        if tags:
            self.tags = tags
        else:
            self.tags = parent.tags

        # Holds a stack of config dicts (partial, rendered). The stack[0][1] entry
        # should always match self.data
        self.stack = [(data, data)]

    @property
    def root(self):
        """Pointer to the root config object."""

        if self.parent is None:
            return self
        return self.parent.root

    def push(self, partial: Mapping):
        """Push and merge a partial config dict into the configuration stack"""
        self._check_root()
        self._merge_data(partial)
        self.stack.insert(0, (partial, self.data))

    def pop(self):
        """Pop the last pushed partial, reverting the config state"""
        self._check_root()
        self.stack.pop()
        _, self.data = self.stack[0]

    def _merge_data(self, partial: Mapping):
        """Merge a partial with the current state"""
        dict_merge.merge(self.data, partial)

    def __getitem__(self, key):
        val = self.data[key]
        return self._parse_value(val)

    def _check_root(self):
        """Check if we're the root config object"""
        if self.parent is not None:
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
            args["root"] = self.root
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
        """Dumps the config object to string

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

        Each entry is loaded in order, using ``fsspec`` and merged into the config
        """

    def load(self, config: Config):
        """Load YAML config entries into a Config object.
        """

        entries = sorted(self.entries, key=lambda x: x[0])
        for entry in entries:
            fs, path = self.get_fs_path(entry)
            content = fs.cat(path)
            data = self.yaml.load(content)
            config.push(data)

        return config

    def get_fs_path(self, entry) -> Tuple[fsspec.AbstractFileSystem, str]:
        """Map an entry URI into
        (*fs*: ``fsspec.AbstractFilesystem``, *path*: ``str``) tuple

        TODO: replace with gamma-fs
        """

        from urllib.parse import urlsplit

        fs = fsspec.filesystem("file")
        path = urlsplit(entry).path
        return fs, path


class MetaConfigLoader(ConfigLoader):
    """A ConfigLoader for the meta config object"""

    @property
    def entries(self) -> List[str]:
        return {f"{PROJECT_HOME}/config/00-meta.yaml"}


class DefaultConfigLoader(ConfigLoader):
    """A ConfigLoader for the ``config/`` folder, supporting environments"""

    @property
    def entries(self) -> List[str]:
        import fsspec

        fs = fsspec.filesystem("file")
        cfg_dir = f"{PROJECT_HOME}/config"

        # default
        files = list(fs.glob(f"{cfg_dir}/*.yaml"))
        files += list(fs.glob(f"{cfg_dir}/*.yml"))

        # environment
        meta = get_meta_config()
        environment = meta["environment"]
        env_dir = f"{cfg_dir}/{environment}"

        if fs.exists(env_dir):
            files += list(fs.glob(f"{env_dir}/*.yaml"))
            files += list(fs.glob(f"{env_dir}/*.yml"))
        else:
            raise EnvironmentFolderException(env_dir)

        # use the file name as sort key, regardless of folder
        files.sort(key=lambda f: f.split("/")[-1])
        files = [f"file://{f}" for f in files]
        return files


_meta_config: Optional[Config] = None
_config: Optional[Config] = None


def reset_config() -> Config:
    global _config
    _config = None


def get_config() -> "Config":
    global _config
    if _config is None:
        from . import tags

        yaml = YAML(typ="rt")
        _config = Config(tags=tags.get_tags(blacklist=True))
        DefaultConfigLoader(yaml=yaml).load(_config)
    return _config


def get_meta_config() -> "Config":
    global _meta_config
    if _meta_config is None:
        yaml = YAML(typ="rt")
        _meta_config = Config(tags=tags.get_tags(blacklist=False))
        MetaConfigLoader(yaml=yaml).load(_meta_config)
    return _meta_config
