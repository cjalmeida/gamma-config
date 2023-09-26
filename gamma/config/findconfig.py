"""Module for discovering configuration files (entries)"""

import logging
import os
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
def get_entries(folder: Path, *, meta_include_folders=True) -> List[Tuple[str, Any]]:
    """Get all entries in a given folder.

    Args:
        meta_include_folder: If `True`, try to load the `XX-meta.yaml` file in the
            folder and follow `include_folder` entries.
    """
    paths = list(folder.glob("*.yaml")) + list(folder.glob("*.yml"))
    entries = [(p.name, p) for p in paths]
    if meta_include_folders:
        meta = load_meta(folder)
        for subfolder in meta["include_folders"]:
            if subfolder is None:
                continue
            subpath = folder / subfolder
            for k, e in get_entries(subpath, meta_include_folders=False):
                entries.append((k, e))

    return entries


@dispatch
def load_meta(config_root: Path) -> ConfigNode:
    """Load the `XX-meta.yaml` file in a given folder"""
    meta_path = list(config_root.glob("*-meta.yaml"))
    if len(meta_path) > 1:
        raise ValueError(f"More than one '*-meta.yaml' in folder: {config_root}")
    with meta_path[0].open("r") as fo:
        return ConfigNode(load_node(fo))


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
        if not _has_meta(root):
            raise ValueError(
                f"Could not find {root}/XX-meta.yaml file as pointed by "
                f"{CONFIG_ROOT_ENV} environment variable"
            )

    return roots


@dispatch
def get_config_roots(_: Literal["LOCAL"]) -> Optional[List[Path]]:
    """Try the path `$PWD/config` as root config folder"""
    root = Path("config").absolute()
    if _has_meta(root):
        return [root]
    return None


@dispatch
def get_config_roots(_: Literal["SET"]) -> Optional[List[Path]]:
    """Try the path `$PWD/config` as root config folder"""

    if CONFIG_ROOT_SET is None:
        return None

    roots = [Path(r).absolute() for r in CONFIG_ROOT_SET]
    for root in roots:
        if not _has_meta(root):
            raise ValueError(
                f"Could not find {root}/XX-meta.yaml file in roots defined via "
                "`set_config_roots`."
            )

    return roots


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
        if _has_meta(candidate):
            return [candidate]
        path = path.parent

    return None


def _has_meta(root: Path):
    return len(list(root.glob("*-meta.yaml"))) > 0


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
