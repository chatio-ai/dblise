from collections.abc import Generator

from contextlib import contextmanager

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

    def _load(self, redis_db: Redis) -> SchemaT:
        return self._converts.deserialize(redis_db.hgetall(self._key_path))

    @override
    def fields(self) -> SchemaT:
        return self._load(self._redis_db)

    def _save(self, redis_db: Redis, instance: SchemaT) -> None:
        mapping = self._converts.serialize(instance)
        missing = self._converts.missing_at(mapping)
        if mapping:
            redis_db.hmset(self._key_path, mapping)
        if missing:
            redis_db.hdel(self._key_path, *missing)

    @override
    def assign(self, instance: SchemaT) -> None:
        with self._redis_db.pipeline() as pipeline:
            self._save(pipeline, instance)
            pipeline.execute()

    @override
    @contextmanager
    def modify(self) -> Generator[SchemaT]:
        with self._redis_db.pipeline() as pipeline:
            pipeline.watch(self._key_path)
            original = self._load(pipeline)
            instance = replace(original)
            yield instance
            if instance != original:
                pipeline.multi()
                self._save(pipeline, instance)
                pipeline.execute()
