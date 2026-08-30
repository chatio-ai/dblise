
from dataclasses import asdict

from decimal import Decimal

from typing import TYPE_CHECKING

from dblise.schemas import Fields
from dblise.helpers import typing
from dblise.helpers import codecs

from .common import FieldDict
from .common import RedisDict


if TYPE_CHECKING:
    type _RedisDict = dict[str | bytes, str]
else:
    _RedisDict = RedisDict


class RedisCodecs[FieldsT: Fields]:

    def __init__(self, data_cls: type[FieldsT], n_digits: int | None = None) -> None:
        self._n_digits = n_digits
        self._data_cls = data_cls
        self._type_ids = typing.field_type_ids(self._data_cls)

    @property
    def data_cls(self) -> type[FieldsT]:
        return self._data_cls

    def missing_at(self, mapping: _RedisDict) -> set[str]:
        return self._type_ids.keys() - mapping.keys()

    def serialize(self, instance: FieldsT) -> _RedisDict:
        mapping = asdict(instance)
        result: _RedisDict = {}
        for name, type_id in self._type_ids.items():
            value = mapping.get(name)
            if value is None:
                continue

            match type_id:
                case _ if type_id.raw_type is str:
                    assert isinstance(value, str)
                    result[name] = value
                case _ if type_id.raw_type is bool:
                    assert isinstance(value, bool)
                    result[name] = str(int(value))
                case _ if type_id.raw_type is int:
                    assert isinstance(value, int)
                    result[name] = str(value)
                case _ if type_id.raw_type is float:
                    assert isinstance(value, float)
                    result[name] = str(value)
                case _ if type_id.raw_type is Decimal:
                    assert isinstance(value, Decimal)
                    result[name] = codecs.decimal_to_str(value, self._n_digits)
                case _:
                    raise TypeError(type_id)

        return result

    def deserialize(self, mapping: RedisDict) -> FieldsT:
        result: FieldDict = {}
        for name, type_id in self._type_ids.items():
            value = mapping.get(name)

            match type_id, value:
                case _, None:
                    result[name] = None if type_id.optional else type_id.raw_type()
                case _ if type_id.raw_type is str:
                    result[name] = value
                case _ if type_id.raw_type is bool:
                    result[name] = bool(int(value))
                case _ if type_id.raw_type is int:
                    result[name] = int(value)
                case _ if type_id.raw_type is float:
                    result[name] = float(value)
                case _ if type_id.raw_type is Decimal:
                    result[name] = codecs.str_to_decimal(value, self._n_digits)
                case _:
                    raise TypeError(type_id)

        return self._data_cls(**result)
