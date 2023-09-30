"""Module for discovering configuration files (entries)"""

import logging
import os
import re
from pathlib import Path
from types import ModuleType
from typing import Literal

from beartype.typing import Any, List, Optional, Tuple

from gamma.config import dispatch

from .confignode import ConfigNode
from .load import load_node

logger = logging.getLogger(__name__)

CONFIG_FIND_ORDER = ["SET", "ENV", "LOCAL", "JUPYTER"]
CONFIG_ROOT_ENV = "GAMMA_CONFIG_ROOT"
CONFIG_ROOT_SET: Optional[List[str]] = None

DEFAULT_META = """
include_folders: !expr env.get('ENVIRONMENT', '').strip().split()
__enable_dot_access__: False
"""
META_PATTERN = r"\d\d-meta\.yaml"


class MissingMetaConfigFile(Exception):
    pass


@dispatch
def get_entries() -> List[Tuple[str, Any]]:
    """Discover the config root folders and get all entries"""
    roots = get_config_roots()
    entries = []
    for root in roots:
        load_dotenv(root)
        entries += get_entries(root) or []
    return entries


@dispatch
def get_entries(folder: Path) -> List[Tuple[str, Any]]:
    """Get all entries in a given folder."""
    paths = list(folder.glob("*.yaml")) + list(folder.glob("*.yml"))
    entries = [(p.name, p) for p in paths if not _is_meta(p)]

    meta = load_meta()
    for subfolder in meta["include_folders"]:
        if subfolder is None:
            continue
        subpath: Path = folder / subfolder
        if subpath.is_dir():
            for k, e in get_entries(subpath):
                entries.append((k, e))

    return entries


def _is_meta(path: Path) -> bool:
    return re.match(META_PATTERN, path.name) is not None


@dispatch
def load_meta() -> dict:
    return load_meta(get_config_roots())


@dispatch
def load_meta(config_roots: List[Path]) -> dict:
    """Load the `XX-meta.yaml` file in a given folder."""

    from . import to_dict
    from .merge import merge_nodes

    meta_paths = []
    for root in config_roots:
        for p in root.glob("*-meta.yaml"):
            if re.match(META_PATTERN, p.name):
                meta_paths.append(p)

    if len(meta_paths) == 0:
        return to_dict(ConfigNode(load_node(DEFAULT_META)))

    elif len(meta_paths) == 1:
        return to_dict(ConfigNode(load_node(meta_paths[0])))

    else:
        meta = [ConfigNode(load_node(p))._node for p in meta_paths]
        _, meta = merge_nodes(meta)
        return to_dict(meta, config=None)


@dispatch
def get_config_roots() -> List[Path]:
    """Return the location for config root path.

    The mechanisms used to find the config root are set in the ``CONFIG_LOAD_ORDER``
    module variable.
    """

    for mechanism in CONFIG_FIND_ORDER:
        roots = get_config_roots(mechanism)
        if roots is not None:
            return roots

    config_folder = Path("config").absolute()
    if config_folder.exists():
        raise MissingMetaConfigFile(
            f"We found a config folder at '{config_folder}' "
            f"but no 'XX-meta.yaml' file. You must have a 'XX-meta.yaml' file at the "
            f"config folder location even if it's empty."
        )

    raise Exception("Cannot locate a gamma config root in any expected location.")


@dispatch
def get_config_roots(_: Literal["ENV"]) -> Optional[List[Path]]:
    f"""Try the path set by {CONFIG_ROOT_ENV} as root config folders.

    Multiple folders can be separated by the `PATH` separator (`os.pathsep`, usually `:`
    in *NIX systems).
    """
    if CONFIG_ROOT_ENV not in os.environ:
        return None

    roots = os.getenv(CONFIG_ROOT_ENV).split(os.pathsep)
    roots = [Path(r).absolute() for r in roots]
    for root in roots:
        if not root.is_dir():
            raise ValueError(
                f"Root candidate '{root}' does not exists or is not a directory. Check "
                f"{CONFIG_ROOT_ENV} environment variable or calls to `set_config_roots`"
                f" and `append_config_root`"
            )

    return roots


@dispatch
def get_config_roots(_: Literal["LOCAL"]) -> Optional[List[Path]]:
    """Try the path `$PWD/config` as root config folder"""
    root = Path("config").absolute()
    if root.is_dir():
        return [root]
    return None


@dispatch
def get_config_roots(_: Literal["SET"]) -> Optional[List[Path]]:
    """Try the path `$PWD/config` as root config folder"""

    if CONFIG_ROOT_SET is None:
        return None

    roots = [Path(r).absolute() for r in CONFIG_ROOT_SET]
    for root in roots:
        if not root.is_dir():
            raise ValueError(
                f"Entry '{root}' is not a directory in roots defined via "
                "`set_config_roots` or `append_config_root`."
            )

    return roots


@dispatch
def set_config_roots(*roots):
    set_config_roots(roots)


@dispatch
def set_config_roots(roots: Optional[List[str]]):
    """Manually set the config roots.

    This function resets the global config.
    """
    from .globalconfig import reset_config

    global CONFIG_ROOT_SET
    CONFIG_ROOT_SET = roots

    reset_config()


@dispatch
def set_config_roots(modules: List[ModuleType]):
    """Manually set the config roots living inside packages.

    This function resets the global config.

    Args:
        modules: List of modules to search for configs.
    """

    from itertools import chain

    paths = [m.__path__ for m in modules]
    paths = list(chain(*paths))
    paths = list(set(paths))
    set_config_roots(paths)


@dispatch
def append_config_root(root: str):
    """Append a root the the set of existing roots.

    This function resets the global config if any root was added.
    """

    from .globalconfig import reset_config

    global CONFIG_ROOT_SET

    CONFIG_ROOT_SET = CONFIG_ROOT_SET or []
    if root not in CONFIG_ROOT_SET:
        CONFIG_ROOT_SET.append(root)

    reset_config()


@dispatch
def append_config_root(module: ModuleType):
    for path in set(module.__path__):
        append_config_root(path)


def is_config_roots_set() -> bool:
    return CONFIG_ROOT_SET is not None


@dispatch
def get_config_roots(_: Literal["JUPYTER"]) -> Optional[List[Path]]:
    """Try `<parent>/config` folders iteratively if we're in a Jupyter (IPython)
    environment"""

    if not _isnotebook():
        return None

    path = Path(".").absolute()
    while path != path.parent:
        candidate = path / "config"
        if candidate.is_dir():
            return [candidate]
        path = path.parent

    return None


def _isnotebook():  # pragma: no cover
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return True  # Terminal running IPython
        else:
            return True  # Other type of IPython kernel (?)
    except NameError:
        return False  # Probably standard Python interpreter


def load_dotenv(root: Path = None):
    """Load dotenv files located in:

    - `$PWD/config.local.env`
    - `{config_root}/../config.local.env`
    - `$PWD/config.env`
    - `{config_root}/../config.env`

    """

    import dotenv

    home = root.parent
    dotenv.load_dotenv("./.env")
    dotenv.load_dotenv(f"{home}/.env")
    dotenv.load_dotenv("./config.local.env")
    dotenv.load_dotenv(f"{home}/config.local.env")
    dotenv.load_dotenv("./config.env")
    dotenv.load_dotenv(f"{home}/config.env")
