
from abc import ABC, abstractmethod

from .schemas import Schema
from .schemas import Entity
from .schemas import Record
from .schemas import Lookup
from .schemas import Scores
from .schemas import Stream


class Facade(ABC):

    @abstractmethod
    def domain(self, key_path: str) -> Entity:
        ...

    @abstractmethod
    def record[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Record[SchemaT]:
        ...

    @abstractmethod
    def lookup[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Lookup[SchemaT]:
        ...

    @abstractmethod
    def scores(self, key_path: str) -> Scores:
        ...

    @abstractmethod
    def stream[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Stream[SchemaT]:
        ...
