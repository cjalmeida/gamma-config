"""Module for discovering configuration files (entries)"""

import logging
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

from gamma.dispatch import Val, dispatch

from .confignode import ConfigNode
from .load import load_node

logger = logging.getLogger(__name__)

FindEnv = Val["env"]
FindLocal = Val["local"]
FindJupyter = Val["jupyter"]

CONFIG_FIND_ORDER = [FindEnv, FindLocal, FindJupyter]
CONFIG_ROOT_ENV = "GAMMA_CONFIG_ROOT"


@dispatch
def get_entries() -> List[Tuple[str, Any]]:
    """Discover the config root folder and get all entries"""
    config_root = get_config_root()
    load_dotenv(config_root)
    return get_entries(config_root)


@dispatch
def get_entries(folder: Path, *, meta_include_folders=True) -> List[Tuple[str, Any]]:
    """Get all entries in a given folder.

    Args:
        meta_include_folder: If `True`, try to load the `00-meta.yaml` file in the
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
    """Load the `00-meta.yaml` file in a given folder"""
    meta_path = config_root / "00-meta.yaml"
    with meta_path.open("r") as fo:
        return ConfigNode(load_node(fo))


@dispatch
def get_config_root() -> Path:
    """Return the location for config root path.

    The mechanisms used to find the config root are set in the ``CONFIG_LOAD_ORDER``
    module variable.
    """

    for mech in CONFIG_FIND_ORDER:
        root = get_config_root(mech())
        if root is not None:
            return root
    raise Exception("Cannot locate a gamma config root in any expected location.")


@dispatch
def get_config_root(_: FindEnv) -> Optional[Path]:
    f"""Try the path set by {CONFIG_ROOT_ENV} as a root config folder"""
    if CONFIG_ROOT_ENV not in os.environ:
        return None

    root = Path(os.getenv(CONFIG_ROOT_ENV)).absolute()
    if not _has_meta(root):
        raise ValueError(
            f"Could not find {root}/00-meta.yaml file as pointed by "
            f"{CONFIG_ROOT_ENV} environment variable"
        )

    return root


@dispatch
def get_config_root(_: FindLocal) -> Optional[Path]:
    """Try the path `$PWD/config` as root config folder"""
    root = Path("config").absolute()
    if _has_meta(root):
        return root
    return None


@dispatch
def get_config_root(_: FindJupyter) -> Optional[Path]:
    """Try `<parent>/config` folders iteratively if we're in a Jupyter (IPython)
    environment"""

    if not _isnotebook():
        return None

    path = Path(".").absolute()
    while path != path.parent:
        candidate = path / "config"
        if _has_meta(candidate):
            return candidate
        path = path.parent

    return None


def _has_meta(root: Path):
    return (root / "00-meta.yaml").exists()


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
    dotenv.load_dotenv("./config.local.env")
    dotenv.load_dotenv(f"{home}/config.local.env")
    dotenv.load_dotenv("./config.env")
    dotenv.load_dotenv(f"{home}/config.env")
