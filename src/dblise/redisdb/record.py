
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import replace

from typing import override

from dblise.schemas import Fields
from dblise.schemas import Result
from dblise.schemas import Record

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisRecord[FieldsT: Fields](RedisEntity, Record[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    def _load(self, redis_db: Redis) -> Result[FieldsT]:
        return Result(redis_db.hgetall(self._key_path), self._converts.deserialize)

    @override
    def value(self) -> Result[FieldsT]:
        return self._load(self._redis_db)

    def _save(self, redis_db: Redis, instance: FieldsT) -> Result[None]:
        async def _func() -> None:
            mapping = self._converts.serialize(instance)
            missing = self._converts.missing_at(mapping)
            if mapping:
                await redis_db.hmset(self._key_path, mapping)
            if missing:
                await redis_db.hdel(self._key_path, *missing)

        return Result(_func(), Result.ASIS)

    @override
    def assign(self, value: FieldsT) -> Result[None]:
        if self._is_piped:
            return self._save(self._redis_db, value)

        async def _func() -> None:
            async with self._redis_db.pipeline() as pipeline:
                await self._save(pipeline, value)
                await pipeline.execute()

        return Result(_func(), Result.ASIS)

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def modify(self) -> AsyncGenerator[FieldsT]:
        if self._is_piped:
            raise RuntimeError
        async with self._redis_db.pipeline() as pipeline:
            await pipeline.watch(self._key_path)
            original = await self._load(pipeline)
            instance = replace(original)
            yield instance
            if instance != original:
                pipeline.multi()
                await self._save(pipeline, instance)
                await pipeline.execute()
