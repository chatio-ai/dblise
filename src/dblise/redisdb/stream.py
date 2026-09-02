
from collections.abc import AsyncIterator

from typing import override

from dblise.schemas import Fields
from dblise.schemas import Result
from dblise.schemas import Stream

from .common import Redis
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
        return Result(self._redis_db.xlen(self._key_path), Result.asis)

    @override
    def __aiter__(self) -> AsyncIterator[FieldsT]:
        return self.values()

    @override
    # pylint: disable=invalid-overridden-method
    async def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> AsyncIterator[FieldsT]:
        async for _, value in self.items(min_id, max_id, count, reverse=reverse):
            yield value

    @override
    # pylint: disable=invalid-overridden-method
    async def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> AsyncIterator[tuple[str, FieldsT]]:
        if min_id is None:
            min_id = '-'
        if max_id is None:
            max_id = '+'
        if reverse:
            min_id, max_id = max_id, min_id

        xrange = self._redis_db.xrevrange if reverse else self._redis_db.xrange
        for key, mapping in await xrange(self._key_path, min_id, max_id, count=count):
            yield key, self._converts.deserialize(mapping)

    @override
    def append(self, value: FieldsT, entry_id: str = '*') -> Result[str]:
        return Result(self._redis_db.xadd(
            self._key_path, self._converts.serialize(value), id=entry_id), Result.asis)

    @override
    def remove(self, entry_id: str) -> Result[bool]:
        return Result(self._redis_db.xdel(self._key_path, entry_id), bool)
