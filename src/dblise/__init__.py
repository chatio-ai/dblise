
from abc import ABC, abstractmethod

from .helpers import typing

from .schemas import Fields
from .schemas import Schema
from .schemas import Entity
from .schemas import Domain
from .schemas import Record
from .schemas import Lookup
from .schemas import Scores
from .schemas import Stream


class Facade(ABC):

    @abstractmethod
    def domain(self, key_path: str) -> Domain:
        ...

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

    def schema[SchemaT: Schema](self, handle: str, schema: type[SchemaT]) -> SchemaT:
        result: dict[str, Entity] = {}
        for name, type_id in typing.key_type_ids(schema).items():
            child = self.handle(handle, name)
            match type_id.entity:
                case _ if type_id.entity is Domain:
                    result[name] = self.domain(child)
                case _ if type_id.entity is Record:
                    assert type_id.fields is not None
                    result[name] = self.record(child, type_id.fields)
                case _ if type_id.entity is Lookup:
                    assert type_id.fields is not None
                    result[name] = self.lookup(child, type_id.fields)
                case _ if type_id.entity is Scores:
                    result[name] = self.scores(child)
                case _ if type_id.entity is Stream:
                    assert type_id.fields is not None
                    result[name] = self.stream(child, type_id.fields)
                case _:
                    raise TypeError(type_id)

        return schema(**result)
