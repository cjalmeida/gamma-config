from typing import Generic, TypeVar
from multimethod import multimethod as dispatch
import types
import inspect

dispatch = dispatch


class ParametricMeta(type):
    def __getitem__(cls, key):
        return cls.of(key)

    def __new__(metacls, name, bases, namespace):
        @classmethod
        def of(cls, *values, name=None):
            if values not in cls._subclasses:
                values_s = ",".join([repr(x) for x in values])
                c_super = f"{cls.__name__}[{values_s}]"
                if name:
                    c_repr = f"Type {name} of {c_super}"
                    c_name = name
                    c_module = inspect.getmodule(inspect.currentframe().f_back).__name__
                else:
                    c_repr = f"Type {c_super}"
                    c_name = c_super
                    c_module = cls.__module__

                SubClass = types.new_class(c_name, (cls,))
                SubClass.__repr__ = lambda *_: c_repr
                SubClass.__module__ = c_module
                SubClass.__values__ = values

                @classmethod
                def _also_of(_, *new_values):
                    cls._subclasses[new_values] = SubClass
                    return SubClass

                SubClass.also_of = _also_of
                cls._subclasses[values] = SubClass
            else:
                SubClass = cls._subclasses[values]
                if name and SubClass.__name__ != name:
                    raise NameError(
                        f"Parametric class with params {values} already instantiated "
                        f"with name {SubClass.__name__}"
                    )

            return SubClass

        @classmethod
        def any_of(cls, *values, name=None):
            first = cls.of(values[0], name=name)
            for alt in values[1:]:
                first.also_of(alt)

        Class = super().__new__(metacls, name, bases, namespace)
        Class._subclasses = dict()
        Class.of = of
        Class.any_of = any_of
        return Class


T = TypeVar("T")


class parametric(Generic[T]):
    def __new__(deco, Class: T) -> T:
        Para = types.new_class(
            Class.__name__, (Class,), kwds={"metaclass": ParametricMeta}
        )
        module = inspect.getmodule(inspect.currentframe().f_back).__name__
        Para.__module__ = module
        return Para

@parametric
class Val:
    """Generic parametric class"""
    pass
