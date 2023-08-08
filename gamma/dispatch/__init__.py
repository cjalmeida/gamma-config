# flake8: noqa

# Big deprecation warning
import warnings

from .dispatchsystem import DispatchError, dispatch
from .parametric_types import ParametricMeta, Val, parametric

warnings.warn(
    "`gamma.dispatch` IS NO LONGER BEING MAINTEINED. We're replacing it with "
    "`plum-dispatch`. If you are using `gamma.dispatch` for extending `gamma.config`, "
    "please replace your `from gamma.dispatch import dispatch` call with "
    "`from gamma.config import dispatch`, per the documentation.",
    DeprecationWarning,
    stacklevel=2,
)


def _isjupyter():  # pragma: no cover
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        return False
    except NameError:
        return False  # Probably standard Python interpreter


def install_breakpoint_hook():
    if _isjupyter():
        # we don't like Jupyter
        return

    import pdb as orig_pdb
    import sys

    pdb = orig_pdb.Pdb(
        skip=["gamma.dispatch.*", "typing", "abc", "inspect", "bdb", "pdb"]
    )
    sys.breakpointhook = pdb.set_trace
