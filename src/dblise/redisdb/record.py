
from collections.abc import Awaitable
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import replace

from typing import override

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Record

from .common import Redis
from .result import RedisResult
from .result import RedisBroker
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisRecord[FieldsT: Fields](RedisEntity, Record[FieldsT]):

    def __init__(self, broker: RedisBroker, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(broker, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    def _load(self, broker: RedisBroker) -> Awaitable[FieldsT]:
        return RedisResult(
            broker, lambda redis: redis.hgetall(self._key_path), self._converts.deserialize)

    @override
    def value(self) -> Awaitable[FieldsT]:
        return self._load(self._broker)

    def _save(self, broker: RedisBroker, instance: FieldsT) -> Awaitable[None]:
        mapping = self._converts.serialize(instance)
        missing = self._converts.missing_at(mapping)

        async def _func(redis: Redis) -> None:
            if mapping:
                await redis.hset(self._key_path, mapping=mapping)
            if missing:
                await redis.hdel(self._key_path, *missing)

        return RedisResult.void(broker, _func)

    @override
    def assign(self, value: FieldsT) -> Awaitable[None]:
        if isinstance(self._broker.client, client.Pipeline):
            return self._save(self._broker, value)

        async def _pipe(redis: Redis) -> None:
            async with redis.pipeline() as pipeline:
                broker = RedisBroker(pipeline)
                self._save(broker, value)
                await broker.commit()
                await pipeline.execute()

        return RedisResult.void(self._broker, _pipe)

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def modify(self) -> AsyncGenerator[FieldsT]:
        if isinstance(self._broker.client, client.Pipeline):
            raise TypeError

        async with self._broker.client.pipeline() as pipeline:
            broker = RedisBroker(pipeline)
            await pipeline.watch(self._key_path)
            original = await self._load(broker)
            instance = replace(original)
            yield instance
            if instance != original:
                pipeline.multi()
                self._save(broker, instance)
                await broker.commit()
                await pipeline.execute()
