"""Definition of base Tag class and standard YAML derived tag types"""
from gamma.dispatch import parametric


@parametric
class Tag:
    @property
    def name(self):
        return str(self.__values__[0])


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
