
from abc import ABC, abstractmethod

from collections.abc import AsyncGenerator
from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Iterator
from collections.abc import Callable

from contextlib import asynccontextmanager

from dataclasses import dataclass


@dataclass
class Fields:
    pass


def _asis[ValueT](value: ValueT) -> ValueT:
    return value


def _void(_value: object) -> None:
    return None


# pylint: disable=too-few-public-methods
class Result[ValueT](Awaitable[ValueT]):
    ASIS = staticmethod(_asis)
    VOID = staticmethod(_void)

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
    def values(self, *, reverse: bool = False) -> Result[Iterator[str]]:
        ...

    @abstractmethod
    def scores(self, *, reverse: bool = False) -> Result[Iterator[tuple[str, float]]]:
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


class Stream[FieldsT](Entity, ABC):
    @abstractmethod
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Iterator[tuple[str, FieldsT]]]:
        ...

    @abstractmethod
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Iterator[FieldsT]]:
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
