
from abc import ABC, abstractmethod

from collections.abc import AsyncGenerator
from collections.abc import AsyncIterator
from collections.abc import AsyncIterable
from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from contextlib import asynccontextmanager

from dataclasses import dataclass


@dataclass
class Fields:
    pass


# pylint: disable=too-few-public-methods
class Result[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        invoke: Awaitable[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._invoke = invoke
        self._decode = decode

    @staticmethod
    def asis(value: ValueT) -> ValueT:
        return value

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke)

    def __await__(self) -> Generator[None, None, ValueT]:
        return self._resolve().__await__()


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
    async def assign(self, value: FieldsT) -> None:
        ...

    @abstractmethod
    @asynccontextmanager
    def modify(self) -> AsyncGenerator[FieldsT]:
        ...


class Lookup[FieldsT](Entity, ABC):
    @abstractmethod
    def lookup(self, key: str) -> Record[FieldsT]:
        ...


class Scores(Entity, AsyncIterable[str], ABC):
    @abstractmethod
    def values(self, *, reverse: bool = False) -> AsyncIterator[str]:
        ...

    @abstractmethod
    def scores(self, *, reverse: bool = False) -> AsyncIterator[tuple[str, float]]:
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
    def insert(
            self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> Result[bool]:
        ...

    @abstractmethod
    def remove(self, key: str) -> Result[bool]:
        ...


class Stream[FieldsT](Entity, AsyncIterable[FieldsT], ABC):
    @abstractmethod
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> AsyncIterator[tuple[str, FieldsT]]:
        ...

    @abstractmethod
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> AsyncIterator[FieldsT]:
        ...

    @abstractmethod
    def len(self) -> Result[int]:
        ...

    @abstractmethod
    def append(self, value: FieldsT, entry_id: str = '*') -> Result[str]:
        ...

    @abstractmethod
    def remove(self, entry_id: str) -> Result[bool]:
        ...


@dataclass(frozen=True)
class Schema:
    pass
