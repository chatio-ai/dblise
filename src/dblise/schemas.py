
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
    async def exists(self) -> bool:
        ...

    @abstractmethod
    async def delete(self) -> bool:
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
    async def index(self, key: str, *, reverse: bool = False) -> int | None:
        ...

    @abstractmethod
    async def score(self, key: str) -> float | None:
        ...

    @abstractmethod
    async def count(self) -> int:
        ...

    @abstractmethod
    async def len(self) -> int:
        ...

    @abstractmethod
    async def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> None:
        ...

    @abstractmethod
    async def remove(self, key: str) -> bool:
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
    async def len(self) -> int:
        ...

    @abstractmethod
    async def append(self, value: FieldsT, entry_id: str = '*') -> str:
        ...

    @abstractmethod
    async def remove(self, entry_id: str) -> bool:
        ...


@dataclass(frozen=True)
class Schema:
    pass
