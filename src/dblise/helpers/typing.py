
from collections.abc import Callable

from dataclasses import is_dataclass
from dataclasses import dataclass
from dataclasses import fields
from dataclasses import Field

from typing import get_type_hints
from typing import get_origin
from typing import get_args

from typing import Union
from typing import Self

from types import UnionType
from types import NoneType

from dblise.schemas import Fields
from dblise.schemas import Entity


@dataclass
class TypeId:
    pass


def _type_ids[TypeIdT: TypeId](cls: type, parse: Callable[[type], TypeIdT]) -> dict[str, TypeIdT]:
    if not is_dataclass(cls):
        raise TypeError(cls)

    hints = get_type_hints(cls)

    def _type_id[T](field: Field[T]) -> TypeIdT:
        return parse(hints[field.name])

    return {field.name: _type_id(field) for field in fields(cls)}


@dataclass
class FieldTypeId(TypeId):
    raw_type: type
    optional: bool

    @classmethod
    def parse(cls, type_def: type) -> Self:
        origin = get_origin(type_def)
        params = get_args(type_def)

        if origin not in (Union, UnionType):
            return cls(raw_type=type_def, optional=False)

        values = tuple(param for param in params if param != NoneType)
        if len(values) != len(params) and len(values) == 1:
            return cls(raw_type=values[0], optional=True)

        raise TypeError(type_def)


def field_type_ids(cls: type) -> dict[str, FieldTypeId]:
    return _type_ids(cls, FieldTypeId.parse)


@dataclass
class KeyTypeId(TypeId):
    entity: type[Entity]
    fields: type[Fields] | None

    @classmethod
    def parse(cls, type_def: type) -> Self:
        origin = get_origin(type_def)
        params = get_args(type_def)

        if not origin:
            return cls(entity=type_def, fields=None)

        if origin and len(params) == 1:
            return cls(entity=origin, fields=params[0])

        raise TypeError(type_def)


def key_type_ids(cls: type) -> dict[str, KeyTypeId]:
    return _type_ids(cls, KeyTypeId.parse)
