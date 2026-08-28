
from dataclasses import dataclass
from dataclasses import Field

from types import UnionType
from types import NoneType


@dataclass
class TypeId:
    raw_type: type
    optional: bool


def find_type[T](field: Field[T]) -> TypeId:
    assert isinstance(field.type, type | UnionType)

    if not isinstance(field.type, UnionType):
        return TypeId(
            raw_type=field.type,
            optional=False,
        )

    if field.type.__args__[1:] == (NoneType,):
        return TypeId(
            raw_type=field.type.__args__[0],
            optional=True,
        )

    raise TypeError
