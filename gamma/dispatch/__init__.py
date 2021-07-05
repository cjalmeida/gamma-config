# flake8: noqa
from .dispatchsystem import DispatchError, dispatch
from .parametric_types import ParametricMeta, Val, parametric


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

    import sys
    import pdb as orig_pdb

    pdb = orig_pdb.Pdb(
        skip=["gamma.dispatch.*", "typing", "abc", "inspect", "bdb", "pdb"]
    )
    sys.breakpointhook = pdb.set_trace
