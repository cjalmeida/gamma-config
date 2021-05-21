# flake8: noqa
import pdb as orig_pdb

from .dispatchsystem import DispatchError, dispatch
from .parametric_types import ParametricMeta, Val, parametric

pdb = orig_pdb.Pdb(skip=["gamma.dispatch.*", "typing", "abc", "inspect", "bdb", "pdb"])


def install_breakpoint_hook():
    import sys

    sys.breakpointhook = pdb.set_trace
