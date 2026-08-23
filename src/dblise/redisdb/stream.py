
from collections.abc import AsyncIterator

from typing import override

from dblise.schemas import Schema
from dblise.schemas import Stream

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisStream[SchemaT: Schema](RedisEntity, Stream[SchemaT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[SchemaT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[SchemaT] = converts

    @override
    async def len(self) -> int:
        return await self._redis_db.xlen(self._key_path)

    @override
    def __aiter__(self) -> AsyncIterator[SchemaT]:
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
    ) -> AsyncIterator[SchemaT]:
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
    ) -> AsyncIterator[tuple[str, SchemaT]]:
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
    async def append(self, instance: SchemaT, entry_id: str = '*') -> str:
        _ = await self._redis_db.xadd(
                self._key_path, self._converts.serialize(instance), id=entry_id)
        assert isinstance(_, str)
        return _

    @override
    async def remove(self, entry_id: str) -> bool:
        return bool(await self._redis_db.xdel(self._key_path, entry_id))
