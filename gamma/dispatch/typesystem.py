"""Module implementing core rules in Julia's dispatch system. For reference,
check Jeff Bezanson's PhD thesis at
https://github.com/JeffBezanson/phdthesis/blob/master/main.pdf
"""

import inspect
import itertools
import typing
from typing import Callable, Iterable, Optional, Tuple, Type, TypeVar, Union

from .poset import VT, PODict, POSet

T = TypeVar("T")


class Vararg:
    pass


class Sig:
    """Represent a Tuple type with extra features, mostly used for method signature
    dispatching"""

    def __init__(self, *types) -> None:
        self.types: Type[Tuple] = Tuple.__getitem__(types)
        self.arg_names: Tuple[str, ...] = tuple(["unset"] * len(types))
        self.func_site: Optional[str] = None

        arity = len(types)
        self.is_variadic: bool = arity and types[-1] is Vararg
        self.min_arity: int = arity - 1 if self.is_variadic else arity

    @property
    def __args__(self) -> Tuple[Type]:
        return self.types.__args__

    def __repr__(self) -> str:
        def name(t):
            origin = getattr(t, "__origin__", None)
            if origin is typing.Union:
                _names = " | ".join(x.__name__ for x in t.__args__)
                return f"[{_names}]"
            elif origin is type:
                return f"Type[{t.__args__[0].__name__}]"
            elif origin:
                return origin.__name__
            elif not hasattr(t, "__name__"):
                return repr(t)
            else:
                return t.__name__

        names = ", ".join(f":{name(t)}" for t in self.types.__args__)
        return f"Sig[{names}]"

    def __hash__(self) -> int:
        return hash(self.types)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Sig):
            return self.types == o.types
        else:
            return self.types == o

    def dump(self) -> str:
        msg = repr(self) + f" at {self.func_site}"
        return msg


def get_origin(t) -> Type:
    if isinstance(t, Sig):
        return tuple

    if getattr(t, "__origin__", None):
        return t.__origin__


def is_variadic(t):
    try:
        return t.is_variadic
    except AttributeError:
        args = getattr(t, "__args__", tuple())
        last = args and t.__args__[-1] or None
        return last and (last is Vararg or getattr(last, "__origin__", None) is Vararg)


def min_arity(t, args, is_variadic):
    try:
        return t.min_arity
    except AttributeError:
        return len(args) - 1 if is_variadic else len(args)


def pad_varargs(a, b) -> Tuple[Tuple[Type], Tuple[Type]]:
    """Extract Tuple args and pad with `object`, accounting for varargs"""

    a_args = a.__args__
    a_var = is_variadic(a)

    b_args = b.__args__
    b_var = is_variadic(b)

    if not (a_var or b_var):
        return a_args, b_args

    na = min_arity(a, a_args, a_var)
    nb = min_arity(b, b_args, b_var)
    nm = max(na, nb)
    a_norm = tuple([*a_args[:na], *([object] * (nm - na))])
    b_norm = tuple([*b_args[:nb], *([object] * (nm - nb))])
    return a_norm, b_norm


def as_typetuple(t):
    return t.types if isinstance(t, Sig) else t


def issubtype(_type: Union[Type, Sig], _super: Union[Type, Sig]):
    """Check if `_type` is a subtype of `_super`.

    Arguments are either `Type` (including parameterized Type) or `Sig` (signature).

    Follow rules in 4.2.2 in Bezanson's thesis.

    Generic (aka parametric) types are invariant. For instance:
        `issubtype(List[int], List[object]) == False`
        `issubtype(List[int], List[int]) == True`
        `issubtype(list, List[object]) == False`

    The exceptions are:
        * `Tuple`: these are covariant. Eg:
            - `issubtype(Tuple[Foo], Tuple[Super]) == True` where `Foo -> Super`

        * `Union`: match if there's a covariant intersection, including non-union types
            - `issubtype(Foo, Union[str, Super]) == True` where `Foo -> Super`
            - `issubtype(str, Union[str, Super]) == True`

        * `typing.Type`: is covariant on the type argument. `type` is treated as
          `typing.Type[object]`
            - `issubtype(typing.Type[str], typing.Type[object]) == True`
            - `issubtype(typing.Type[str], type) == True`

    Since Python don't tag container instances with the type paramemeters
    (eg. `type([1,2,3]) == list`) this means that we can't dispatch lists as we would
    with arrays in Julia. The multiple dispatch system must then erase method signature
    generic information for such container types.

    See the `parametric` module for a way to declare and dispatch on parametric types.

    Also, we don't currently support the equivalent of `UnionAll`. This is not an issue
    since we don't support parametric dispatch, ie. `TypeVar`s in method signatures.
    """

    # quick test of equality
    if _type is _super:
        return True

    if _type == _super:
        return True

    # quick test of subclass
    try:
        if issubclass(_type, _super):
            return True
    except TypeError:
        pass

    # normalize Type[type]
    _type = typing.Type[object] if _type is type else _type
    _super = typing.Type[object] if _super is type else _super

    type_orig = get_origin(_type)
    super_orig = get_origin(_super)

    if (
        type_orig == super_orig
        and type_orig in (tuple, type)
        and super_orig in (tuple, type)
    ):
        # normalize params accounting for varargs
        type_params, super_params = pad_varargs(_type, _super)
        # check component-wise, Tuple types are covariant
        return len(type_params) == len(super_params) and all(
            issubtype(t, s) for (t, s) in zip(type_params, super_params)
        )

    elif type_orig is Union and super_orig is Union and _type == _super:
        # quick check for union equality
        return True

    elif type_orig is Union or super_orig is Union:
        # check for subtypes the rule is return true if there's a subtype relation
        # in the product of the parameters
        type_params = _type.__args__ if type_orig is Union else [_type]
        super_params = _super.__args__ if super_orig is Union else [_super]
        for (a, b) in itertools.product(type_params, super_params):
            if a is b or issubtype(a, b):
                return True
        return False

    return False


def is_more_specific(a, b):
    a_sub_b = issubtype(a, b)
    b_sub_a = issubtype(b, a)

    if a_sub_b and b_sub_a:
        if is_variadic(b):
            return True

    if b_sub_a:
        return False

    if a_sub_b:
        return True

    tag_a = getattr(a, "__tag__", None)
    tag_b = getattr(b, "__tag__", None)
    if tag_a is not None and tag_b is not None:
        return issubclass(tag_a, tag_b) and not issubclass(tag_b, tag_a)

    return False


def signatures_from(func: Callable) -> Iterable[Sig]:
    """Parse a callable to extract the dispatchable type tuple."""

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
        if origin and origin not in (typing.Union, type):
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

        sig = Sig(*_types)
        sig.arg_names = tuple(_names)

        code = func.__code__
        sig.func_site = f"{code.co_filename}:{code.co_firstlineno}"

        yield sig

        if params and params[-1].default != inspect.Parameter.empty:
            stack.append(params[:-1])


class SigDict(PODict[Sig, VT]):
    def __init__(self, data=None) -> None:
        super().__init__(data=data, lt=is_more_specific)


class SigSet(POSet[Sig]):
    def __init__(self, data) -> None:
        super().__init__(data=data, lt=is_more_specific)
