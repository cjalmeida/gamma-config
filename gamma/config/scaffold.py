"""Module to 'scaffold' append bootstrap config for gamma-io"""
import shutil
from pathlib import Path
from typing import NamedTuple

import pkg_resources

import colorama
from colorama import Fore, Style
from gamma.dispatch import dispatch

ENTRYPOINT_GROUP = "gamma.config.scaffold"


class GammaConfigScaffold(NamedTuple):
    name = "gamma-config"


@dispatch
def get_source(module: GammaConfigScaffold):
    return Path(__file__).parent / "sample"


@dispatch
def get_files(module, src):
    return sorted(src.glob("**/*"))


def scaffold(target, force):
    """Initialize the config folder with samples.

    The set of files to be deployed on scaffolding can be extended via the Python
    "entrypoint" plugin system.

    First you need to add your the directives in `setup.cfg` pointing to the
    `gamma.config.scaffold` group. Example:

    ```ini
    [options.entry_points]
    gamma.config.scaffold =
        gamma-io = gamma.io.scaffold:setup
    ```

    In the example above, `setup` function under `gamma.io.scaffold` module should
    return an instance of any class that will be used for dispatching the `get_files`
    and `get_source` functions.
    """

    colorama.init()  # for fellow windows users

    if not target:
        target = Path(".").absolute()

    print(f"TARGET: {target}")
    target = Path(target)
    confdir: Path = target / "config"
    confdir.mkdir(exist_ok=True)

    # load plugins from ENTRYPOINT_GROUP
    modules = [GammaConfigScaffold()]
    for entry in pkg_resources.iter_entry_points(ENTRYPOINT_GROUP):
        plugin = entry.load()
        modules.append(plugin())

    # find source under sample folder
    for mod in modules:
        src = get_source(mod)
        for srcfile in get_files(mod, src):
            # Check if target file already exists
            relfile = srcfile.relative_to(src)
            dstfile: Path = confdir / relfile
            if srcfile.is_dir():
                continue
            elif not force and dstfile.exists():
                print(
                    Fore.YELLOW + f"[{mod.name}] File '{relfile}' already exists "
                    "and --force was not set",
                    Style.RESET_ALL,
                )
            else:
                dstfile.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(srcfile, dstfile)
                _file = Fore.CYAN + str(relfile) + Style.RESET_ALL
                print(
                    f"[{mod.name}] copied file {_file} to",
                    str(confdir.relative_to(target)),
                )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize config folder with samples"
    )
    parser.add_argument(
        "-t",
        "--target",
        help="The target folder. Default to current folder.",
        default=None,
    )
    parser.add_argument(
        "--force",
        help="If set, do not check for existing files.",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()
    from gamma.config.scaffold import scaffold as _run

    _run(args.target, args.force)
