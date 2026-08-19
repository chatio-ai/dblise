from abc import ABC, abstractmethod

from collections.abc import Generator
from collections.abc import Iterator
from collections.abc import Iterable

from contextlib import contextmanager

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


class Domain(Entity, ABC):
    pass


class Record[SchemaT](Entity, ABC):
    @abstractmethod
    def fields(self) -> SchemaT:
        ...

    @abstractmethod
    def assign(self, instance: SchemaT) -> None:
        ...

    @abstractmethod
    @contextmanager
    def modify(self) -> Generator[SchemaT]:
        ...


class Lookup[SchemaT](Entity, ABC):
    @abstractmethod
    def lookup(self, key: str) -> Record[SchemaT]:
        ...


class Scores(Entity, Iterable[str], ABC):
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
    def len(self) -> int:
        ...

    @abstractmethod
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> None:
        ...

    @abstractmethod
    def remove(self, key: str) -> bool:
        ...


class Stream[SchemaT](Entity, Iterable[SchemaT], ABC):
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
    def len(self) -> int:
        ...

    @abstractmethod
    def append(self, instance: SchemaT, entry_id: str = '*') -> str:
        ...

    @abstractmethod
    def remove(self, entry_id: str) -> bool:
        ...
