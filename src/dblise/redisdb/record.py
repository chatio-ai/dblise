
from collections.abc import Awaitable
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import replace

from typing import override

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Record

from .common import Redis
from .common import Pipeline
from .result import RedisResult
from .result import RedisEngine
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisRecord[FieldsT: Fields](RedisEntity, Record[FieldsT]):

    def __init__(self, engine: RedisEngine, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(engine, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    def _load(self, engine: RedisEngine, redis_db: Redis) -> Awaitable[FieldsT]:
        return RedisResult(
            engine, redis_db.hgetall(self._key_path), self._converts.deserialize)

    @override
    def value(self) -> Awaitable[FieldsT]:
        return self._load(self._engine, self._engine.client)

    def _save(self, engine: RedisEngine, redis_db: Pipeline, instance: FieldsT) -> Awaitable[None]:
        mapping = self._converts.serialize(instance)
        missing = self._converts.missing_at(mapping)
        if mapping:
            redis_db.hmset(self._key_path, mapping)
        if missing:
            redis_db.hdel(self._key_path, *missing)

        return RedisResult.void(engine, engine.client)

    @override
    def assign(self, value: FieldsT) -> Awaitable[None]:
        if isinstance(self._engine.client, client.Pipeline):
            return self._save(self._engine, self._engine.client, value)

        async def _func() -> None:
            async with self._engine.client.pipeline() as pipeline:
                engine = RedisEngine(pipeline)
                self._save(engine, pipeline, value)
                await pipeline.execute()

        return RedisResult.void(self._engine, _func())

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def modify(self) -> AsyncGenerator[FieldsT]:
        if isinstance(self._engine.client, client.Pipeline):
            raise TypeError

        async with self._engine.client.pipeline() as pipeline:
            engine = RedisEngine(pipeline)
            await pipeline.watch(self._key_path)
            original = await self._load(engine, pipeline)
            instance = replace(original)
            yield instance
            if instance != original:
                pipeline.multi()
                self._save(engine, pipeline, instance)
                await pipeline.execute()
