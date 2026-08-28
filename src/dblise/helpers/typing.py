
from dataclasses import Field

from types import UnionType
from types import NoneType


def find_type[T](field: Field[T]) -> tuple[type, bool]:
    assert isinstance(field.type, type | UnionType)

    if not isinstance(field.type, UnionType):
        return field.type, False

    if field.type.__args__[1:] == (NoneType,):
        return field.type.__args__[0], True

    raise TypeError
