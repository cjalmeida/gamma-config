# flake8: noqa
from .dispatchsystem import DispatchError, dispatch
from .parametric_types import ParametricMeta, Val, parametric


def install_breakpoint_hook():
    import sys
    import pdb as orig_pdb

    pdb = orig_pdb.Pdb(
        skip=["gamma.dispatch.*", "typing", "abc", "inspect", "bdb", "pdb"]
    )
    sys.breakpointhook = pdb.set_trace
