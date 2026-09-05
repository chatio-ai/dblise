
from abc import ABC, abstractmethod

from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from collections.abc import Iterator

from contextlib import asynccontextmanager

from dataclasses import dataclass


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
    def exists(self) -> Awaitable[bool]:
        ...

    @abstractmethod
    def delete(self) -> Awaitable[bool]:
        ...


class Record[FieldsT](Entity, ABC):
    @abstractmethod
    def value(self) -> Awaitable[FieldsT]:
        ...

    @abstractmethod
    def assign(self, value: FieldsT) -> Awaitable[None]:
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
    def values(self, *, reverse: bool = False) -> Awaitable[Iterator[str]]:
        ...

    @abstractmethod
    def scores(self, *, reverse: bool = False) -> Awaitable[Iterator[tuple[str, float]]]:
        ...

    @abstractmethod
    def index(self, key: str, *, reverse: bool = False) -> Awaitable[int | None]:
        ...

    @abstractmethod
    def score(self, key: str) -> Awaitable[float | None]:
        ...

    @abstractmethod
    def count(self) -> Awaitable[int]:
        ...

    @abstractmethod
    def len(self) -> Awaitable[int]:
        ...

    @abstractmethod
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False,
               ) -> Awaitable[bool]:
        ...

    @abstractmethod
    def remove(self, key: str) -> Awaitable[bool]:
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
    ) -> Awaitable[Iterator[tuple[str, FieldsT]]]:
        ...

    @abstractmethod
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Awaitable[Iterator[FieldsT]]:
        ...

    @abstractmethod
    def len(self) -> Awaitable[int]:
        ...

    @abstractmethod
    def append(self, value: FieldsT, entry_id: str = '*') -> Awaitable[str]:
        ...

    @abstractmethod
    def remove(self, entry_id: str) -> Awaitable[bool]:
        ...


@dataclass(frozen=True)
class Schema:
    pass
