from typing import Mapping, Tuple

from pydantic import BaseModel


class DictConfigType(BaseModel):
    __discriminator__ = "kind"

    @classmethod
    def get_subclasses(cls):
        stack = [cls]
        while stack:
            cc = stack.pop(0)
            for sub in cc.__subclasses__():
                stack.append(sub)
                yield sub

    @classmethod
    def parse_scalar(cls, value):
        kind = value
        args = {cls.__discriminator__: value}
        return kind, args

    @classmethod
    def get_discr_value(cls):
        disc = cls.__discriminator__
        try:
            kind = getattr(cls, disc)
            return kind
        except AttributeError:
            pass

        try:
            _field = cls.__fields__[disc]
            kind = getattr(_field, "default", None)
            if kind is None:
                raise ValueError(f"Field {cls.__name__}.{disc} has no value set")
            return kind
        except KeyError:
            pass

        raise ValueError(f"Type '{cls.__name__}' missing field '{disc}' ")

    @classmethod
    def parse_obj(cls, obj):
        if not isinstance(obj, Mapping):
            ret = cls.parse_scalar(obj)
            if isinstance(ret, Tuple):
                kind, args = ret
            else:
                return ret
        else:
            try:
                kind = obj[cls.__discriminator__]
                args = obj
            except KeyError:
                raise ValueError(f"Missing '{cls.__discriminator__}' field.")

        match = [k for k in cls.get_subclasses() if k.get_discr_value() == kind]
        if not match:
            raise ValueError(f"No {cls.__name__} for kind '{kind}'")
        return match[0](**args)

    @classmethod
    def __get_validators__(cls):
        yield cls.parse_obj
