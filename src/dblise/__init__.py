
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from typing import Self
from typing import cast

from .helpers import typing

from .schemas import Fields
from .schemas import Schema
from .schemas import Entity
from .schemas import Record
from .schemas import Lookup
from .schemas import Scores
from .schemas import Stream


class Facade(ABC):

    @abstractmethod
    def record[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Record[FieldsT]:
        ...

    @abstractmethod
    def lookup[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Lookup[FieldsT]:
        ...

    @abstractmethod
    def scores(self, handle: str) -> Scores:
        ...

    @abstractmethod
    def stream[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Stream[FieldsT]:
        ...

    @abstractmethod
    def handle(self, parent: str, child: str) -> str:
        ...

    def _entity(self, handle: str, type_id: typing.KeyTypeId) -> Entity:
        match type_id:
            case _ if type_id.entity is Record:
                assert type_id.fields is not None
                return self.record(handle, type_id.fields)
            case _ if type_id.entity is Lookup:
                assert type_id.fields is not None
                return self.lookup(handle, type_id.fields)
            case _ if type_id.entity is Scores:
                return self.scores(handle)
            case _ if type_id.entity is Stream:
                assert type_id.fields is not None
                return self.stream(handle, type_id.fields)
            case _:
                raise TypeError(type_id)

    def entity[EntityT: Entity](self, handle: str, entity: type[EntityT]) -> EntityT:
        type_id = typing.KeyTypeId.parse(entity)
        return cast(EntityT, self._entity(handle, type_id))

    def schema[SchemaT: Schema](self, handle: str, schema: type[SchemaT]) -> SchemaT:
        result: dict[str, Entity] = {}
        for name, type_id in typing.key_type_ids(schema).items():
            result[name] = self._entity(self.handle(handle, name), type_id)

        return schema(**result)

    @abstractmethod
    async def exists(self, schema: Schema) -> bool:
        ...

    @abstractmethod
    async def delete(self, schema: Schema) -> bool:
        ...

    @abstractmethod
    @asynccontextmanager
    def pipeline(self) -> AsyncGenerator[Self]:
        ...
