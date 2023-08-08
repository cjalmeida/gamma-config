"""Definition of base Tag class and standard YAML derived tag types"""
from plum import parametric, type_parameter


@parametric
class Tag:
    @property
    def name(self):
        return str(type_parameter(self))


Map = Tag["tag:yaml.org,2002:map"]
Seq = Tag["tag:yaml.org,2002:seq"]
Str = Tag["tag:yaml.org,2002:str"]
Int = Tag["tag:yaml.org,2002:int"]
Float = Tag["tag:yaml.org,2002:float"]
Bool = Tag["tag:yaml.org,2002:bool"]
Timestamp = Tag["tag:yaml.org,2002:timestamp"]
Null = Tag["tag:yaml.org,2002:null"]
Merge = Tag["tag:yaml.org,2002:merge"]


class TagException(Exception):
    pass
