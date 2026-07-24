
from abc import ABC, abstractmethod

from collections.abc import Iterator
from collections.abc import Iterable
from collections.abc import Sized

from contextlib import AbstractContextManager

from dataclasses import dataclass


@dataclass
class Schema:
    pass


class Entity(ABC):
    @abstractmethod
    def exists(self) -> bool:
        ...

    @abstractmethod
    def delete(self) -> bool:
        ...


class Record[SchemaT](Entity, AbstractContextManager[SchemaT], ABC):
    @abstractmethod
    def fields(self) -> SchemaT:
        ...


class Lookup[SchemaT](Entity, ABC):
    @abstractmethod
    def lookup(self, key: str) -> Record[SchemaT]:
        ...


class Scores(Entity, Sized, Iterable[str], ABC):
    @abstractmethod
    def values(self, *, reverse: bool = False) -> Iterator[str]:
        ...

    @abstractmethod
    def scores(self, *, reverse: bool = False) -> Iterator[tuple[str, float]]:
        ...

    @abstractmethod
    def index(self, key: str, *, reverse: bool = False) -> int | None:
        ...

    @abstractmethod
    def score(self, key: str) -> float | None:
        ...

    @abstractmethod
    def count(self) -> int:
        ...

    @abstractmethod
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> None:
        ...

    @abstractmethod
    def remove(self, key: str) -> bool:
        ...


class Stream[SchemaT](Entity, Sized, Iterable[SchemaT], ABC):
    @abstractmethod
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Iterator[tuple[str, SchemaT]]:
        ...

    @abstractmethod
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Iterator[SchemaT]:
        ...

    @abstractmethod
    def append(self, instance: SchemaT, entry_id: str = '*') -> None:
        ...

    @abstractmethod
    def remove(self, entry_id: str) -> bool:
        ...
