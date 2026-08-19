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

    def _load(self, redis_db: Redis | None = None) -> SchemaT:
        if redis_db is None:
            redis_db = self._redis_db
        return self._converts.deserialize(redis_db.hgetall(self._key_path))

    @override
    def fields(self) -> SchemaT:
        return self._load()

    @override
    def assign(self, instance: SchemaT) -> None:
        self._redis_db.hmset(self._key_path, self._converts.serialize(instance))

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
                pipeline.unlink(self._key_path)
                pipeline.hmset(self._key_path, self._converts.serialize(instance))
                pipeline.execute()
