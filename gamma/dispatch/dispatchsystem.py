import functools
import inspect
import typing
import warnings
from collections import defaultdict
from typing import Callable, Dict, Iterable, List, Set, Tuple

from .typesystem import Sig, SigDict, is_more_specific, issubtype, signatures_from


class DispatchError(Exception):
    pass


class OverwriteWarning(UserWarning):
    pass


def methods_matching(call, table) -> List:
    """Given a method table, return the methods matching the call signature.

    Args:
        table: an iterable of methods ordered by `is_more_specific`
        call: the call signature as a `Sig` object or `Tuple[...]` type
    """
    matches = [x for x in table if issubtype(call, x)]
    methods = []
    while matches:
        match = matches[0]
        methods.append(match)
        matches = [x for x in matches[1:] if not is_more_specific(match, x)]
    return methods


def get_type(val):
    if isinstance(val, type) and getattr(val, "__valuetype__", False):
        return val
    elif isinstance(val, type):
        return typing.Type[val]
    else:
        return type(val)


_namespaces = dict()


class dispatch:
    """Function wrapper to dispatch methods.

    Args:
        namespace: If set, use a shared namespace with `namespace` as key, otherwise
            try to find matching functions in `locals`.
        specialize: If set, will throw an error if this function is not a specialization
            of an already existing function.
        overwrite: When `True`, won't issue a warning about overwriting a method.
    """

    #: Pending methods register due to forward references
    pending: Set

    #: The methods table for this function
    methods: SigDict[Callable]

    #: Cache from call signature to actual function
    cache: Dict[Tuple, Callable]

    #: Callable to get types from function arguments
    get_type: Callable

    #: function name
    name: str

    #: set of reserved argument names
    arg_names: Dict[str, List[Sig]]

    def __new__(cls, *args, namespace=None, specialize=False, overwrite=False):
        if isinstance(namespace, str):
            namespace: dict = _namespaces.setdefault(namespace, {})
            add_to_namespace = True
        else:
            namespace = inspect.currentframe().f_back.f_locals
            add_to_namespace = False

        def wrapped(func):
            # check if function with the same name exists in scope
            existing = namespace.get(func.__name__)
            if existing and isinstance(existing, dispatch):
                existing.register(func, overwrite=overwrite)
                return existing

            if specialize:
                raise DispatchError(
                    f"This method has `specialize=True` but no existing "
                    f"function named `{func.__name__}` exists."
                )

            # create a new dispatch table wrapper
            self: dispatch = functools.update_wrapper(object.__new__(cls), func)
            self.pending = set()
            self.get_type = get_type
            self.methods = SigDict()
            self.cache = dict()
            self.name = func.__name__
            self.arg_names = defaultdict(list)
            self.register(func, overwrite=overwrite)

            _dispatch_by_name[self.name] = self

            if add_to_namespace:
                namespace[func.__name__] = self

            return self

        if args and callable(args[0]):
            return wrapped(args[0])

        return wrapped

    def register(
        self, func: Callable, *, overwrite=False, allow_pending=True
    ) -> Callable:
        """Register a new method to this function's dispatch table.

        Args:
            func: the method to register
            overwrite: if False, will warn if the registration will overwrite and
                existing registration.
            allow_pending: if True, won't error on forward references
        """
        self.clear()
        try:
            for sig in signatures_from(func):
                self._register_single(sig, func, overwrite)
                for name in sig.arg_names:
                    lst = self.arg_names[name]
                    try:
                        lst.remove(sig)
                    except ValueError:
                        pass
                    lst.append(sig)
            return self
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

    def _warn_overwrite(self, new: Sig, old: Sig):
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
        """Manually map a call signature to a callable"""

        self.clear()
        if not key:
            return
        key = key if isinstance(key, tuple) else (key,)
        sig = Sig(*key)
        self._register_single(sig, func, False)

    def __delitem__(self, types: Tuple):
        """Remove a method registration"""
        self.clear()
        sig = Sig(*types)
        self.methods.pop(sig)

    def __getitem__(self, key: Tuple):
        return self.find_method(key)

    def find_method(self, key: Tuple) -> Callable:
        """Find and cache the next applicable method of given types.

        Args:
            key: A call args types tuple.
        """

        # ensure tuple of types
        if getattr(key, "__origin__", None) is tuple:
            key = key.__args__
        elif not isinstance(key, tuple):
            if isinstance(key, Iterable):
                key = tuple(*key)
            else:
                key = tuple([key])

        self.resolve_pending()
        cached = self.cache.get(key)
        if cached:
            return cached

        call_sig = Sig(*key)

        match = methods_matching(call_sig, self.methods)
        if not match:
            self._except_no_method_found(key)

        if len(match) > 1:
            self._except_no_meet(key, match)

        method = self.methods[match[0]]

        # cache and return
        self.cache[key] = method
        return method

    def _except_no_meet(self, key, match: List[Sig]):
        names = ", ".join(":" + t.__name__ for t in key)
        msg = f"Method call ({names}) is ambiguous. Candidates:"
        for m in match:
            msg += f"\n    {m} at {m.func_site}"
        raise DispatchError(msg)

    def _except_no_method_found(self, key):
        names = ", ".join(":" + getattr(t, "__name__", repr(t)) for t in key)
        msg = f"{self}: no method found for call ({names})"
        msg = self._msg_multiple_definitions_same_name(msg, key)
        raise DispatchError(msg)

    def _msg_multiple_definitions_same_name(self, msg, key):
        other = []
        for name, _dispatch in _dispatch_by_name.items():
            if name == self.name and _dispatch is not self:
                other.append(_dispatch.find_method(key))

        if other:
            msg += (
                "\n\nNote: found maching method(s) with the same name "
                "but in another module. This may be an error due to a missing import."
            )
            for func in other:
                co = func.__code__
                msg += f"\n\n    -> {co.co_filename}:{co.co_firstlineno}"

            msg += "\n"
        return msg

    def __call__(self, *args, **kwargs):
        """Resolve and dispatch to best method."""
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
                if "keyword argument" not in ex.args[0]:
                    raise
                file = func.__code__.co_filename
                line = func.__code__.co_firstlineno
                msg = f"{ex.args[0]}\n    in function {file}:{line}"
                raise TypeError(msg) from ex

        except DispatchError as ex:
            file = inspect.currentframe().f_back.f_code.co_filename
            line = inspect.currentframe().f_back.f_lineno
            msg = f"{ex.args[0]}\n    called from {file}:{line}"
            raise DispatchError(msg) from ex

    def _check_invalid_kwargs(self, kwargs):
        """Check if we're passing 'reserved' arg names in kwargs.

        Python allows passing positional args as kwargs. This effectively forbid this,
        ie. all keyword call arguments are deemed to be kwargs, and this is required to
        avoid weird behavior.

        Example:

            @dispatch
            def foo(a: int, *, b):
                return "ok"

            assert foo(1, b=1) == "ok"
            assert foo(1, b="foo") == "ok"
            assert foo(a=1, b=1) == "ok"   # <- this is not allowed
        """

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


_dispatch_by_name: Dict[str, dispatch] = defaultdict(lambda: [])
