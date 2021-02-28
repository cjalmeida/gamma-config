from gamma.dispatch import parametric
from typing import Union


@parametric
class Tag:
    @property
    def name(self):
        return self.__value__


Map = Tag.of("tag:yaml.org,2002:map")
Seq = Tag.of("tag:yaml.org,2002:seq")
Str = Tag.of("tag:yaml.org,2002:str")
Int = Tag.of("tag:yaml.org,2002:int")
Float = Tag.of("tag:yaml.org,2002:float")
Bool = Tag.of("tag:yaml.org,2002:bool")
Timestamp = Tag.of("tag:yaml.org,2002:timestamp")
Null = Tag.of("tag:yaml.org,2002:null")


class TagException(Exception):
    pass
