
from abc import ABC, abstractmethod

from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from collections.abc import Sequence

from contextlib import asynccontextmanager

from dataclasses import dataclass


type Result[ValueT] = Awaitable[ValueT]


@dataclass
class Fields:
    pass


class Entity(ABC):

    @property
    @abstractmethod
    def handle(self) -> str:
        ...

    @property
    @abstractmethod
    def fields(self) -> type[Fields] | None:
        ...

    @abstractmethod
    def exists(self) -> Result[bool]:
        ...

    @abstractmethod
    def delete(self) -> Result[bool]:
        ...


class Record[FieldsT](Entity, ABC):
    @abstractmethod
    def value(self) -> Result[FieldsT]:
        ...

    @abstractmethod
    def assign(self, value: FieldsT) -> Result[None]:
        ...

    @abstractmethod
    @asynccontextmanager
    def modify(self) -> AsyncGenerator[FieldsT]:
        ...


class Lookup[FieldsT](Entity, ABC):
    @abstractmethod
    def lookup(self, key: str) -> Record[FieldsT]:
        ...


class Scores(Entity, ABC):
    @abstractmethod
    def values(self, *, reverse: bool = False) -> Result[Sequence[str]]:
        ...

    @abstractmethod
    def scores(self, *, reverse: bool = False) -> Result[Sequence[tuple[str, float]]]:
        ...

    @abstractmethod
    def index(self, key: str, *, reverse: bool = False) -> Result[int | None]:
        ...

    @abstractmethod
    def score(self, key: str) -> Result[float | None]:
        ...

    @abstractmethod
    def count(self) -> Result[int]:
        ...

    @abstractmethod
    def len(self) -> Result[int]:
        ...

    @abstractmethod
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False,
               ) -> Result[bool]:
        ...

    @abstractmethod
    def remove(self, *keys: str) -> Result[int]:
        ...


class Stream[FieldsT](Entity, ABC):
    @abstractmethod
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Sequence[tuple[str, FieldsT]]]:
        ...

    @abstractmethod
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Sequence[FieldsT]]:
        ...

    @abstractmethod
    def len(self) -> Result[int]:
        ...

    @abstractmethod
    def append(self, value: FieldsT, entry_id: str = '*') -> Result[str]:
        ...

    @abstractmethod
    def remove(self, *entry_ids: str) -> Result[int]:
        ...


@dataclass(frozen=True)
class Schema:
    pass
