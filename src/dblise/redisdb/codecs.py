
from dataclasses import asdict
from dataclasses import fields

from decimal import Decimal

from typing import TYPE_CHECKING

from dblise.schemas import Schema
from dblise.helpers import typing
from dblise.helpers import codecs

from .common import FieldDict
from .common import RedisDict


if TYPE_CHECKING:
    type _RedisDict = dict[str | bytes, str]
else:
    _RedisDict = RedisDict


class RedisCodecs[SchemaT: Schema]:

    def __init__(self, obj_type: type[SchemaT], n_digits: int | None = None) -> None:
        self._n_digits = n_digits
        self._obj_type = obj_type

    def missing_at(self, mapping: _RedisDict) -> list[str]:
        return [field.name for field in fields(self._obj_type) if field.name not in mapping]

    def serialize(self, instance: SchemaT) -> _RedisDict:
        mapping = asdict(instance)
        result: _RedisDict = {}
        for field in fields(self._obj_type):
            value = mapping.get(field.name)
            if value is None:
                continue

            type_id = typing.find_type(field)
            match type_id:
                case _ if type_id.raw_type is str:
                    assert isinstance(value, str)
                    result[field.name] = value
                case _ if type_id.raw_type is bool:
                    assert isinstance(value, bool)
                    result[field.name] = str(int(value))
                case _ if type_id.raw_type is int:
                    assert isinstance(value, int)
                    result[field.name] = str(value)
                case _ if type_id.raw_type is float:
                    assert isinstance(value, float)
                    result[field.name] = str(value)
                case _ if type_id.raw_type is Decimal:
                    assert isinstance(value, Decimal)
                    result[field.name] = codecs.decimal_to_str(value, self._n_digits)
                case _:
                    raise TypeError(type_id)

        return result

    def deserialize(self, mapping: RedisDict) -> SchemaT:
        result: FieldDict = {}
        for field in fields(self._obj_type):
            value = mapping.get(field.name)

            type_id = typing.find_type(field)
            match type_id, value:
                case _, None:
                    result[field.name] = None if type_id.optional else type_id.raw_type()
                case _ if type_id.raw_type is str:
                    result[field.name] = value
                case _ if type_id.raw_type is bool:
                    result[field.name] = bool(int(value))
                case _ if type_id.raw_type is int:
                    result[field.name] = int(value)
                case _ if type_id.raw_type is float:
                    result[field.name] = float(value)
                case _ if type_id.raw_type is Decimal:
                    result[field.name] = codecs.str_to_decimal(value, self._n_digits)
                case _:
                    raise TypeError(type_id)

        return self._obj_type(**result)
