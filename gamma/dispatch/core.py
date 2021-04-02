import functools
import inspect
import typing
import warnings
import itertools
from collections import defaultdict
from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from collections.abc import MutableMapping

__all__ = ["dispatch"]


class DispatchError(Exception):
    pass


class OverwriteWarning(UserWarning):
    pass


class Vararg:
    pass


KT = TypeVar("KT")
VT = TypeVar("VT")


class PODict(MutableMapping, Generic[KT, VT]):
    """Dictionary that stores keys sorted (like a prio queue) that works
    for partial orders"""

    data: List[Tuple[KT, VT]]
    __unset = object()

    def __init__(self, data=None) -> None:
        self.data = []
        if data:
            # initialize
            items = getattr(data, "items", lambda: data)
            for k, v in items():
                self[k] = v

    def __setitem__(self, key: KT, value: VT) -> None:
        for i, (k, _) in enumerate(self.data):
            if key == k:
                self.data.pop(i)
                self.data.insert(i, (key, value))
                return
            elif key < k:
                self.data.insert(i, (key, value))
                return
        self.data.append((key, value))

    def __getitem__(self, key: KT) -> VT:
        for (k, v) in self.data:
            if key == k:
                return v
        raise KeyError(key)

    def pop(self, key: KT, default=__unset) -> VT:
        try:
            item = self.popitem(key)
        except KeyError:
            if default is self.__unset:
                raise
            return default
        else:
            return item[1]

    def popitem(self, key: KT, default=__unset) -> Tuple[KT, VT]:
        for i, (k, v) in enumerate(self.data):
            if key == k:
                self.data.pop(i)
                return k, v

        if default is not self.__unset:
            return default
        raise KeyError(key)

    def __iter__(self):
        return self.keys()

    def __len__(self) -> int:
        return self.data.__len__()

    def __delitem__(self, key: KT) -> None:
        for i, (k, _) in enumerate(self.data):
            if key == k:
                self.data.pop(i)
                return

    def keys(self) -> Iterable[KT]:
        return (x[0] for x in self.data)

    def items(self) -> Iterable[KT]:
        return iter(self.data)

    def values(self) -> Iterable[VT]:
        return (x[1] for x in self.data)

    def __contains__(self, o) -> bool:
        return o in self.keys()

    def clear(self) -> None:
        return self.data.clear()


class POSet(PODict, MutableSet):
    def __init__(self, data) -> None:
        self.data = []
        if data:
            for v in data:
                self.add(v)

    def add(self, value) -> None:
        self[value] = None

    def discard(self, value) -> None:
        del self[value]


def get_union_args(t: Type) -> Optional[Type]:
    if getattr(t, "__origin__", None) is Union:
        return t.__args__
    return None


def issametype(this, other):
    if this is other:
        return True

    this = get_union_args(this) or [this]
    other = get_union_args(other) or [other]
    for (a, b) in itertools.product(this, other):
        if a is b:
            return True
    return False


def methods_for(call, table) -> List[Callable]:
    matches = [x for x in table if call <= x]
    methods = []
    while matches:
        match = matches[0]
        methods.append(match)
        matches = [x for x in matches[1:] if not (match < x)]
    return methods


def issubtype(this, other, strict: bool = False):
    """Check if `this` is a subtype of `other`

    For Union types, this is true if any element in `this` union is subtype of any
    member of `other` union.

    Args:
        strict: Do a strict subtype check if True
    """

    this = get_union_args(this) or [this]
    other = get_union_args(other) or [other]

    if len(this) == 1 and len(other) == 1:
        return issubclass(this[0], other[0]) and not (strict and this[0] is other[0])
    else:
        for (a, b) in itertools.product(this, other):
            if issubtype(a, b, strict):
                return True
        return False


class DispatchSignature:
    """This represents a tuple of types with extra information for debugging"""

    param_types: Tuple[Type]
    arg_names: Tuple[str]
    func_site: Optional[str] = None
    isvariadic: bool
    min_arity: int

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

            arity = len(_types)
            self.isvariadic = arity and _types[-1] is Vararg
            self.min_arity = arity - 1 if self.isvariadic else arity

            code = func.__code__
            self.func_site = f"{code.co_filename}:{code.co_firstlineno}"

            yield self

            if params and params[-1].default != inspect.Parameter.empty:
                stack.append(params[:-1])

    def __init__(self, param_types: Tuple[Type]) -> None:
        self.param_types = param_types
        arity = len(param_types)
        self.isvariadic = arity and param_types[-1] is Vararg
        self.min_arity = arity - 1 if self.isvariadic else arity

    def _pad(self, n):
        ptypes = self.param_types[:-1] if self.isvariadic else self.param_types
        pad = n - len(ptypes)
        return tuple([*ptypes, *([object] * pad)])

    def __eq__(self, o: object) -> bool:
        self_types = self.param_types
        other_types = getattr(o, "param_types", None)

        if other_types is None:
            return False

        if len(self_types) != len(other_types):
            return False

        if self_types == other_types:
            return True

        # this breaks __hash__ contract
        if all(issametype(a, b) for (a, b) in zip(self_types, other_types)):
            return True

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

    def _normalize(self, other: "DispatchSignature") -> bool:
        if any((self.isvariadic, other.isvariadic)):
            n = max(self.min_arity, other.min_arity)
            self_types = self._pad(n) if self.isvariadic else self.param_types
            other_types = other._pad(n) if other.isvariadic else other.param_types
            return self_types, other_types
        else:
            return self.param_types, other.param_types

    def __le__(self, other: "DispatchSignature") -> bool:
        """Check if self tuple type is a subtype of other tuple type or equal"""
        self_types, other_types = self._normalize(other)
        if len(self_types) != len(other_types):
            return False

        return all(issubtype(s, o) for (s, o) in zip(self_types, other_types))

    def __lt__(self, other: "DispatchSignature") -> bool:
        """Check if self tuple type is a strict subtype of other tuple type"""
        self_types, other_types = self._normalize(other)
        if len(self_types) != len(other_types):
            return False

        le = all(issubtype(s, o) for (s, o) in zip(self_types, other_types))
        if not le:
            return False

        # check for equality
        return not all(issametype(s, o) for (s, o) in zip(self_types, other_types))

    def dump(self) -> str:
        msg = repr(self) + f" at {self.func_site}"
        return msg


class dispatch:
    """Function wrapper to dispatch methods"""

    pending: Set
    methods: PODict[DispatchSignature, Callable]
    cache: Dict[Tuple, Callable]
    get_type: Callable
    name: str
    arg_names: Dict[str, List[DispatchSignature]]

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
            self.methods = PODict()
            self.cache = dict()
            self.name = func.__name__
            self.arg_names = defaultdict(list)
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
                self._register_single(sig, func, overwrite)
                for name in sig.arg_names:
                    lst = self.arg_names[name]
                    try:
                        lst.remove(sig)
                    except ValueError:
                        pass
                    lst.append(sig)

        except NameError:
            if allow_pending:
                self.pending.add((func, overwrite))
            else:
                raise

    def _register_single(self, sig, func, overwrite):
        old, _ = self.methods.popitem(sig, (None, None))
        if old is not None and not overwrite:
            self._warn_overwrite(sig, old)
        self.methods[sig] = func

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
        self._register_single(sig, func, False)

    def __delitem__(self, types: Tuple):
        self.clear()
        sig = DispatchSignature(types)
        self.methods.pop(sig)

    def __getitem__(self, key: Tuple):
        return self.find_method(key)

    def find_method(self, key: Tuple) -> Callable:
        """Find and cache the next applicable method of given types.

        Args:
            key: A call args types tuple.
        """
        self.resolve_pending()
        cached = self.cache.get(key)
        if cached:
            return cached

        call_sig = DispatchSignature(key)

        match = methods_for(call_sig, self.methods)
        if not match:
            self._except_no_method_found(key)

        if len(match) > 1:
            self._except_no_meet(key, match)

        method = self.methods[match[0]]

        # cache and return
        self.cache[key] = method
        return method

    def _except_no_meet(self, key, match: List[DispatchSignature]):
        names = ", ".join(":" + t.__name__ for t in key)
        msg = f"Method call ({names}) is ambiguous. Candidates:"
        for m in match:
            msg += f"\n    {m} at {m.func_site}"
        raise DispatchError(msg)

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
        for sig in self.methods:
            msg += "\n    " + sig.dump()
        return msg

    def __repr__(self) -> str:
        n = len(self.methods)
        p = ""
        if n == 1:
            p = "(s)"
        return f"<function '{self.__name__}' with {n} method{p}>"
