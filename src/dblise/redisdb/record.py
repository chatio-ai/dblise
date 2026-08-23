
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import replace

from typing import override

from dblise.schemas import Schema
from dblise.schemas import Record

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisRecord[SchemaT: Schema](RedisEntity, Record[SchemaT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[SchemaT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[SchemaT] = converts

    async def _load(self, redis_db: Redis) -> SchemaT:
        return self._converts.deserialize(await redis_db.hgetall(self._key_path))

    @override
    async def fields(self) -> SchemaT:
        return await self._load(self._redis_db)

    async def _save(self, redis_db: Redis, instance: SchemaT) -> None:
        mapping = self._converts.serialize(instance)
        missing = self._converts.missing_at(mapping)
        if mapping:
            await redis_db.hmset(self._key_path, mapping)
        if missing:
            await redis_db.hdel(self._key_path, *missing)

    @override
    async def assign(self, instance: SchemaT) -> None:
        async with self._redis_db.pipeline() as pipeline:
            await self._save(pipeline, instance)
            await pipeline.execute()

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def modify(self) -> AsyncGenerator[SchemaT]:
        async with self._redis_db.pipeline() as pipeline:
            await pipeline.watch(self._key_path)
            original = await self._load(pipeline)
            instance = replace(original)
            yield instance
            if instance != original:
                pipeline.multi()
                await self._save(pipeline, instance)
                await pipeline.execute()
