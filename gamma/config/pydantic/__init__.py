from typing import Mapping, Optional, Tuple

from pydantic import BaseModel

NO_DISCRIMINATOR = object()


class ConfigStruct(BaseModel):
    __discriminator__ = "kind"

    @classmethod
    def get_subclasses(cls):
        yield cls
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
        key = cls.__discriminator__
        try:
            value = getattr(cls, key)
            return value
        except AttributeError:
            pass

        try:
            _field = cls.__fields__[key]
            value = getattr(_field, "default", None)
            if value is None:
                raise ValueError(f"Field {cls.__name__}.{key} has no value set")
            return value
        except KeyError:
            pass

        return NO_DISCRIMINATOR

    @classmethod
    def parse_obj(cls, obj):
        if not isinstance(obj, Mapping):
            ret = cls.parse_scalar(obj)
            if isinstance(ret, Tuple):
                discr, args = ret
            else:
                return ret
        else:
            try:
                discr = obj[cls.__discriminator__]
                args = obj
            except KeyError:
                raise ValueError(f"Missing '{cls.__discriminator__}' field.")

        _type = cls.find_type(discr)
        return _type(**args)

    @classmethod
    def find_type(cls, discr):
        match = [k for k in cls.get_subclasses() if k.get_discr_value() == discr]
        if not match:
            raise ValueError(
                f"No {cls.__name__} for {cls.__discriminator__} = '{discr}'"
            )
        return match[0]

    @classmethod
    def __get_validators__(cls):
        yield cls.parse_obj

    class Config:
        frozen = True


class URIConfigStruct(ConfigStruct):
    __discriminator__ = "scheme"
    scheme: str
    uri: Optional[str]

    @classmethod
    def parse_obj(cls, obj):
        if isinstance(obj, Mapping):
            if "uri" in obj and cls.__discriminator__ not in obj:
                scheme, _ = cls.split_uri(obj["uri"])
                obj["scheme"] = scheme

            if "uri" in obj and hasattr(obj, "update"):
                obj2 = cls.parse_uri(obj["uri"]).dict()
                obj.update(obj2)

        return super().parse_obj(obj)

    @staticmethod
    def split_uri(value):
        value = str(value)
        if ":" not in value:
            raise ValueError(f"'{value}' not a valid URI: missing ':'")
        return value.split(":", 1)

    @classmethod
    def parse_scalar(cls, value):
        scheme, _ = cls.split_uri(value)
        _type: URIConfigStruct = cls.find_type(scheme)
        return _type.parse_uri(value)

    @classmethod
    def parse_uri(cls, uri: str):
        return cls(uri=uri)
