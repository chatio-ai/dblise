
from dataclasses import asdict
from dataclasses import fields

from decimal import Decimal

from types import UnionType
from types import NoneType

from typing import TYPE_CHECKING

from dblise.schemas import Schema

from .common import FieldDict
from .common import RedisDict


if TYPE_CHECKING:
    type _RedisDict = dict[str | bytes, str]
else:
    _RedisDict = RedisDict


def str_to_decimal(value: str, n_digits: int | None = None) -> Decimal:
    num = Decimal(value)
    return num if n_digits is None else round(num, n_digits)


def decimal_to_str(num: Decimal, n_digits: int | None = None) -> str:
    num = num if n_digits is None else round(num, n_digits)
    return format(num.normalize(), 'zf')


class RedisCodecs[SchemaT: Schema]:

    def __init__(self, obj_type: type[SchemaT], n_digits: int | None = None) -> None:
        self._n_digits = n_digits
        self._obj_type = obj_type

    def _find_type(self, field: type | UnionType) -> tuple[type, bool]:
        if not isinstance(field, UnionType):
            return field, False

        if field.__args__[1:] == (NoneType,):
            return field.__args__[0], True

        raise TypeError

    def missing_at(self, mapping: _RedisDict) -> list[str]:
        return [field.name for field in fields(self._obj_type) if field.name not in mapping]

    def serialize(self, instance: SchemaT) -> _RedisDict:
        mapping = asdict(instance)
        result: _RedisDict = {}
        for field in fields(self._obj_type):
            value = mapping.get(field.name)
            if value is None:
                continue

            assert isinstance(field.type, type | UnionType)
            raw_type, optional = self._find_type(field.type)
            match raw_type:
                case _ if raw_type is str:
                    assert isinstance(value, str)
                    result[field.name] = value
                case _ if raw_type is bool:
                    assert isinstance(value, bool)
                    result[field.name] = str(int(value))
                case _ if raw_type is int:
                    assert isinstance(value, int)
                    result[field.name] = str(value)
                case _ if raw_type is float:
                    assert isinstance(value, float)
                    result[field.name] = str(value)
                case _ if raw_type is Decimal:
                    assert isinstance(value, Decimal)
                    result[field.name] = decimal_to_str(value, self._n_digits)
                case _:
                    raise TypeError(raw_type, optional)

        return result

    def deserialize(self, mapping: RedisDict) -> SchemaT:
        result: FieldDict = {}
        for field in fields(self._obj_type):
            value = mapping.get(field.name)

            assert isinstance(field.type, type | UnionType)
            raw_type, optional = self._find_type(field.type)

            match raw_type, value:
                case _, None:
                    result[field.name] = None if optional else raw_type()
                case _ if raw_type is str:
                    result[field.name] = value
                case _ if raw_type is bool:
                    result[field.name] = bool(int(value))
                case _ if raw_type is int:
                    result[field.name] = int(value)
                case _ if raw_type is float:
                    result[field.name] = float(value)
                case _ if raw_type is Decimal:
                    result[field.name] = str_to_decimal(value, self._n_digits)
                case _:
                    raise TypeError(raw_type, optional)

        return self._obj_type(**result)
