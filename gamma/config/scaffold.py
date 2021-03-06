import os
import shutil
import colorama
from colorama import Fore, Style


def scaffold(target, force):
    """Initialize the config folder with samples"""

    from pathlib import Path

    colorama.init()  # for fellow windows users

    if not target:
        target = Path(".").absolute()

    print(f"TARGET: {target}")
    target = Path(target)
    confdir: Path = target / "config"
    meta: Path = confdir / "00-meta.yaml"

    # find source under sample folder
    src = Path(__file__).parent / "sample"

    # Check if config/00-meta.yaml already exists
    if not force and meta.exists():
        print(
            Fore.YELLOW + "ERROR: File 'config/00-meta.yaml' already exists "
            "and --force was not set",
            Style.RESET_ALL,
        )
        raise SystemExit(1)

    confdir.mkdir(exist_ok=True)
    _recursive_copy(src, confdir)
    print(
        Fore.YELLOW + "Copied config samples to:",
        Fore.CYAN + str(confdir),
        Style.RESET_ALL,
    )


def _recursive_copy(src, dest):
    """
    Copy each file from src dir to dest dir, including sub-directories.
    """
    for item in os.listdir(src):
        file_path = os.path.join(src, item)

        # if item is a file, copy it
        if os.path.isfile(file_path):
            shutil.copy(file_path, dest)

        # else if item is a folder, recurse
        elif os.path.isdir(file_path):
            new_dest = os.path.join(dest, item)
            os.mkdir(new_dest)
            _recursive_copy(file_path, new_dest)


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
    scaffold(args.target, args.force)
