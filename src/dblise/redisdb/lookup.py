
from collections.abc import Awaitable
from typing import override

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Lookup

from .result import RedisEngine
from .codecs import RedisCodecs
from .entity import RedisEntity
from .record import RedisRecord


class RedisLookup[FieldsT: Fields](RedisEntity, Lookup[FieldsT]):

    def __init__(self, engine: RedisEngine, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(engine, key_path)
        self._converts = converts
        self._key_glob = f'{key_path}:*'

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    @override
    def lookup(self, key: str) -> Record[FieldsT]:
        return RedisRecord(self._engine, f'{self._key_path}:{key}', self._converts)

    async def _exists(self) -> bool:
        async for _ in self._engine.client.scan_iter(self._key_glob):
            return True
        return False

    @override
    def exists(self) -> Awaitable[bool]:
        if isinstance(self._engine.client, client.Pipeline):
            raise NotImplementedError
        return self._exists()

    async def _delete(self) -> bool:
        keys = [_ async for _ in self._engine.client.scan_iter(self._key_glob)]
        if keys:
            await self._engine.client.unlink(*keys)
        return bool(keys)

    @override
    def delete(self) -> Awaitable[bool]:
        if isinstance(self._engine.client, client.Pipeline):
            raise NotImplementedError
        return self._delete()
