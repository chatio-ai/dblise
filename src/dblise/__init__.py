
from abc import ABC, abstractmethod

from .schemas import Fields
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
    def record[FieldsT: Fields](self, key_path: str, fields: type[FieldsT]) -> Record[FieldsT]:
        ...

    @abstractmethod
    def lookup[FieldsT: Fields](self, key_path: str, fields: type[FieldsT]) -> Lookup[FieldsT]:
        ...

    @abstractmethod
    def scores(self, key_path: str) -> Scores:
        ...

    @abstractmethod
    def stream[FieldsT: Fields](self, key_path: str, fields: type[FieldsT]) -> Stream[FieldsT]:
        ...
