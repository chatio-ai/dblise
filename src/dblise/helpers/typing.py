
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import Field

from typing import Self

from types import UnionType
from types import NoneType


@dataclass
class TypeId:
    raw_type: type
    optional: bool

    @classmethod
    def parse(cls, type_def: type | UnionType) -> Self:

        if not isinstance(type_def, UnionType):
            return cls(
                raw_type=type_def,
                optional=False,
            )

        if type_def.__args__[1:] == (NoneType,):
            return cls(
                raw_type=type_def.__args__[0],
                optional=True,
            )

        raise TypeError


def type_ids(cls: type) -> dict[str, TypeId]:
    def _type_id[T](field: Field[T]) -> TypeId:
        assert isinstance(field.type, type | UnionType)
        return TypeId.parse(field.type)

    return {field.name: _type_id(field) for field in fields(cls)}
