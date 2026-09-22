
from collections.abc import Awaitable
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextlib import nullcontext
from dataclasses import replace

from typing import override

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Record

from .common import Redis
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
        return broker.cast(lambda redis: redis.hgetall(self._key_path), self._converts.deserialize)

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

        return broker.bulk(_func)

    @override
    def assign(self, value: FieldsT) -> Awaitable[None]:
        return self._save(self._broker, value)

    @asynccontextmanager
    async def _pipeline(self) -> AsyncGenerator[RedisBroker]:
        async with self._broker.client.pipeline() as pipeline:
            broker = RedisBroker(pipeline)
            yield broker
            await broker.execute()

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def modify(self) -> AsyncGenerator[FieldsT]:
        async with ((
            nullcontext(self._broker) if
            isinstance(self._broker.client, client.Pipeline)
            else self._pipeline()
        ) as broker):
            await broker.watch(self._key_path)
            original = await self._load(broker)
            instance = replace(original)
            yield instance
            if instance != original:
                self._save(broker, instance)
