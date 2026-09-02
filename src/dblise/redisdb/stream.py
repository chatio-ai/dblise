
from collections.abc import Awaitable
from collections.abc import Iterator

from typing import override

from dblise.schemas import Fields
from dblise.schemas import Result
from dblise.schemas import Stream

from .common import Redis
from .common import RedisDict
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisStream[FieldsT: Fields](RedisEntity, Stream[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    @override
    def len(self) -> Result[int]:
        return Result(self._redis_db.xlen(self._key_path), Result.ASIS)

    def _range(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Awaitable[Iterator[tuple[str, RedisDict]]]:
        if min_id is None:
            min_id = '-'
        if max_id is None:
            max_id = '+'
        if reverse:
            min_id, max_id = max_id, min_id

        xrange = self._redis_db.xrevrange if reverse else self._redis_db.xrange
        return xrange(self._key_path, min_id, max_id, count=count)

    @override
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Iterator[FieldsT]]:
        def _iter(it: Iterator[tuple[str, RedisDict]]) -> Iterator[FieldsT]:
            for _, value in it:
                yield self._converts.deserialize(value)

        return Result(self._range(min_id, max_id, count, reverse=reverse), _iter)

    @override
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Result[Iterator[tuple[str, FieldsT]]]:
        def _iter(it: Iterator[tuple[str, RedisDict]]) -> Iterator[tuple[str, FieldsT]]:
            for key, value in it:
                yield key, self._converts.deserialize(value)

        return Result(self._range(min_id, max_id, count, reverse=reverse), _iter)

    @override
    def append(self, value: FieldsT, entry_id: str = '*') -> Result[str]:
        return Result(self._redis_db.xadd(
            self._key_path, self._converts.serialize(value), id=entry_id), Result.ASIS)

    @override
    def remove(self, entry_id: str) -> Result[bool]:
        return Result(self._redis_db.xdel(self._key_path, entry_id), bool)
