
from dataclasses import replace

from types import TracebackType

from typing import override

from dblise.schemas import Schema
from dblise.schemas import Record

from .common import Redis
from .common import Pipeline
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisRecord[SchemaT: Schema](RedisEntity, Record[SchemaT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[SchemaT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[SchemaT] = converts

        self._original: SchemaT | None = None
        self._instance: SchemaT | None = None

        self._pipeline: Pipeline | None = None

    def _load(self, redis_db: Redis | None = None) -> SchemaT:
        if redis_db is None:
            redis_db = self._redis_db
        return self._converts.deserialize(redis_db.hgetall(self._key_path))

    def _open(self) -> SchemaT:
        if self._pipeline is not None:
            raise RuntimeError

        self._pipeline = self._redis_db.pipeline()
        self._pipeline.watch(self._key_path)

        return self._load(self._pipeline)

    def _save(self, instance: SchemaT) -> None:
        if self._pipeline is None:
            raise RuntimeError

        self._pipeline.multi()
        self._pipeline.delete(self._key_path)
        self._pipeline.hmset(self._key_path, self._converts.serialize(instance))
        self._pipeline.execute()

    def _drop(self) -> None:
        if self._pipeline is None:
            return

        try:
            self._pipeline.reset()
        finally:
            self._pipeline = None

    @override
    def fields(self) -> SchemaT:
        return self._load()

    @override
    def __enter__(self) -> SchemaT:
        if self._instance is not None:
            raise RuntimeError

        try:
            self._original = self._open()
            self._instance = replace(self._original)
        except BaseException:
            self._drop()
            raise

        return self._instance

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._instance is None:
            return

        try:
            if exc_value is None and self._instance != self._original:
                self._save(self._instance)
        finally:
            self._original = None
            self._instance = None

            self._drop()
