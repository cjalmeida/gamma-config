import functools
import inspect
import typing
import warnings
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Type, Union

__all__ = ["dispatch"]


class DispatchError(Exception):
    pass


class OverwriteWarning(UserWarning):
    pass


class Vararg:
    pass


# marker indicating not dispatchable
NO_DISPATCH = (2 ** 16) - 1

# to support dynamic subclass check, assign a high distance to
# subclasses not on the MRO
DYN_SUBCLASS_DISTANCE = 99


def _distance(subclass: type, cls) -> int:
    """Return estimated distance between classes, based on MRO."""
    if getattr(cls, "__origin__", None) is typing.Union:
        return min(_distance(subclass, arg) for arg in cls.__args__)
    mro = type.mro(subclass)
    try:
        return mro.index(cls)
    except ValueError:
        if issubclass(subclass, cls):
            return DYN_SUBCLASS_DISTANCE
        return NO_DISPATCH


class DispatchSignature:

    param_types: Tuple[Type]
    arg_names: Set[str]
    func_site: Optional[str] = None

    @classmethod
    def from_callable(cls, func: Callable) -> Iterable["DispatchSignature"]:

        hints = typing.get_type_hints(func)
        kinds = {
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
        }

        def get_type(p: inspect.Parameter):
            if p.kind == inspect.Parameter.VAR_POSITIONAL:
                return Vararg
            _type = hints.get(p.name, object)
            origin = getattr(_type, "__origin__", None)
            if origin and origin is not typing.Union:
                return origin
            return _type

        params = list(
            p for p in inspect.signature(func).parameters.values() if p.kind in kinds
        )
        stack = [params]
        while stack:
            _types = []
            _names = []
            params = stack.pop()
            for p in params:
                _types.append(get_type(p))
                _names.append(p.name)

            self: DispatchSignature = object.__new__(cls)
            self.param_types = tuple(_types)
            self.arg_names = tuple(_names)
            code = func.__code__
            self.func_site = f"{code.co_filename}:{code.co_firstlineno}"
            yield self

            if params and params[-1].default != inspect.Parameter.empty:
                stack.append(params[:-1])

    def __init__(self, param_types: Tuple[Type]) -> None:
        self.param_types = param_types

    def expand_args(self, n):
        ptypes = self.param_types
        if ptypes and ptypes[-1] is Vararg and n >= (len(ptypes) - 1):
            pad = n - len(self.param_types) + 1
            return tuple([*self.param_types[:-1], *([object] * pad)])
        return ptypes

    def strip_args(self):
        ptypes = self.param_types
        if ptypes and ptypes[-1] is Vararg:
            return ptypes[:-1]
        return ptypes

    def distance(self, other: "DispatchSignature") -> Union[Tuple, int]:
        """Give the relative dispatch "distance"between `self` other `other`

        Dispatch rules:
            - arguments must be of same length (accounting for variadic expansion)
            - all `other` param types must be an instance of `self` param types

        If `other` is not a dispatch match, this returns `NO_DISPATCH`
        """
        other_types = other.strip_args()
        n = len(other_types)
        self_types = self.expand_args(n)

        if len(self_types) != n:
            return NO_DISPATCH

        res = tuple(_distance(o, s) for (o, s) in zip(other_types, self_types))
        if NO_DISPATCH in res:
            return NO_DISPATCH

        return res

    def __hash__(self) -> int:
        return hash(self.param_types)

    def __eq__(self, o: object) -> bool:
        return self.param_types == getattr(o, "param_types", None)

    def __repr__(self) -> str:
        def name(t):
            origin = getattr(t, "__origin__", None)
            if origin is typing.Union:
                _names = " | ".join(x.__name__ for x in t.__args__)
                return f"[{_names}]"
            elif origin:
                return origin.__name__
            return t.__name__

        names = ", ".join(f":{name(t)}" for t in self.param_types)
        return f"<sig ({names})>"

    def dump(self) -> str:
        msg = repr(self) + f" at {self.func_site}"
        return msg


class dispatch:
    """Function wrapper to dispatch methods"""

    pending: Set
    signatures: Dict[DispatchSignature, Callable]
    cache: Dict[Tuple, Callable]
    get_type: Callable
    name: str
    arg_names: Dict[str, Set[DispatchSignature]]

    def __new__(cls, *args, overwrite=False):
        namespace = inspect.currentframe().f_back.f_locals

        def wrapped(func):
            # check if function with the same name exists in scope
            existing = namespace.get(func.__name__)
            if existing and isinstance(existing, dispatch):
                existing.register(func, overwrite=overwrite)
                return existing

            # create a new dispatch table wrapper
            self: dispatch = functools.update_wrapper(object.__new__(cls), func)
            self.pending = set()
            self.get_type = type
            self.signatures = dict()
            self.cache = dict()
            self.name = func.__name__
            self.arg_names = defaultdict(set)
            self.register(func, overwrite=overwrite)
            return self

        if args and callable(args[0]):
            return wrapped(args[0])

        return wrapped

    def register(
        self, func: Callable, *, overwrite=False, allow_pending=True
    ) -> Callable:
        self.clear()
        try:
            for sig in DispatchSignature.from_callable(func):
                if not overwrite:
                    if sig in self.signatures:
                        old = [x for x in self.signatures if x == sig][0]
                        self._warn_overwrite(sig, old)
                self.signatures[sig] = func
                for name in sig.arg_names:
                    self.arg_names[name].add(sig)
        except NameError:
            if allow_pending:
                self.pending.add((func, overwrite))
            else:
                raise

    def _warn_overwrite(self, new: DispatchSignature, old: DispatchSignature):
        msg = (
            f"Method for function '{self.name}' defined\n"
            f"    at {old.func_site}\n"
            f"will be overwritten by new method defined\n"
            f"    at {new.func_site}\n"
            f"If using kw-or-positional vs kw-only arguments correctly."
        )
        warnings.warn(msg, OverwriteWarning)

    def clear(self):
        """Empty the cache."""
        self.cache.clear()

    def __setitem__(self, key, func: Callable):
        self.clear()
        if not key:
            return
        key = key if isinstance(key, tuple) else (key,)
        sig = DispatchSignature(key)
        self.signatures[sig] = func

    def __delitem__(self, types: Tuple):
        self.clear()
        sig = DispatchSignature(types)
        self.signatures.pop(sig, None)

    def __getitem__(self, key: Tuple):
        return self.find_method(key)

    def find_method(self, key: Tuple) -> Callable:
        """Find and cache the next applicable method of given types.

        Args:
            key: A call args types.
        """
        self.resolve_pending()
        cached = self.cache.get(key)
        if cached:
            return cached

        call_sig = DispatchSignature(key)

        candidates = []
        for msig in self.signatures:
            d = msig.distance(call_sig)
            if d != NO_DISPATCH:
                candidates.append((d, msig))

        if not candidates:
            self._except_no_method_found(key)

        candidates.sort()
        best_sig = self._get_meet(candidates, key)
        method = self.signatures[best_sig]

        # cache and return
        self.cache[key] = method
        return method

    def _get_meet(self, oset: List[Tuple[Tuple, DispatchSignature]], key):
        """Get the "meet" of a set, eg. the element that is lower than everyone else.

        When the dispatch is ambiguous, there's distance set is partially ordered and
        may not have a meet.
        """

        if len(oset) == 1:
            return oset[0][1]

        def is_le(a, b):
            return all(x <= y for x, y in zip(a, b))

        meet = None
        for (z, z_sig) in oset:
            valid = True
            for (w, _) in oset:
                valid &= is_le(z, w)
                if not valid:
                    break
            if valid:
                meet = z_sig
                break

        if not meet:
            names = ", ".join(":" + t.__name__ for t in key)
            msg = f"Method call ({names}) is ambiguous. Candidates:"
            c: DispatchSignature
            for (_, c) in oset:
                msg += f"\n    {c} at {c.func_site}"
            raise DispatchError(msg)

        return meet

    def _except_no_method_found(self, key):
        names = ", ".join(":" + t.__name__ for t in key)
        msg = f"{self}: no method found for call ({names})"
        raise DispatchError(msg)

    def __call__(self, *args, **kwargs):
        """Resolve and dispatch to best method.

        Dispatch rules should match Julia's.
        """
        try:
            if kwargs:
                self._check_invalid_kwargs(kwargs)
            key = tuple(self.get_type(a) for a in args)
            func = self.cache.get(key)
            if not func:
                func = self.find_method(key)

            try:
                return func(*args, **kwargs)
            except TypeError as ex:
                file = func.__code__.co_filename
                line = func.__code__.co_firstlineno
                msg = f"{ex.args[0]}\n    in function {file}:{line}"
                raise DispatchError(msg) from ex

        except DispatchError as ex:
            file = inspect.currentframe().f_back.f_code.co_filename
            line = inspect.currentframe().f_back.f_lineno
            msg = f"{ex.args[0]}\n    called from {file}:{line}"
            raise DispatchError(msg) from ex

    def _check_invalid_kwargs(self, kwargs):
        isec = set(kwargs).intersection(self.arg_names)
        if isec:
            msg = (
                f"Reserved argument names were used as keywords in "
                f"method call: {isec}"
            )
            for arg in isec:
                msg += f"\n    '{arg}' in signatures:"
                for sig in self.arg_names[arg]:
                    msg += f"\n        '{sig.dump()}'"

            raise DispatchError(msg)

    def resolve_pending(self):
        """Evaluate any pending forward references.

        This can be called explicitly when using forward references,
        otherwise cache misses will evaluate.
        """
        while self.pending:
            func, overwrite = self.pending.pop()
            self.register(func, overwrite=overwrite, allow_pending=False)

    def dump(self) -> str:  # pragma: no cover
        """Pretty-print debug information about this function"""
        msg = repr(self) + " with signatures:"
        for sig in self.signatures:
            msg += "\n    " + sig.dump()
        return msg

    def __repr__(self) -> str:
        n = len(self.signatures)
        p = ""
        if n == 1:
            p = "(s)"
        return f"<function '{self.__name__}' with {n} method{p}>"
