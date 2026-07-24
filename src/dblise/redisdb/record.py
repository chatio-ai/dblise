
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

    def _load(self) -> SchemaT:
        return self._converts.deserialize(self._redis_db.hgetall(self._key_path))

    def _open(self) -> SchemaT:
        self._pipeline = self._redis_db.pipeline()
        self._pipeline.watch(self._key_path)

        return self._load()

    def _save(self, instance: SchemaT) -> None:
        if self._pipeline is None:
            raise RuntimeError

        self._pipeline.multi()
        self._pipeline.delete(self._key_path)
        self._pipeline.hmset(self._key_path, self._converts.serialize(instance))
        self._pipeline.execute()

    def _drop(self) -> None:
        if self._pipeline is None:
            raise RuntimeError

        self._pipeline.unwatch()

    @override
    def fields(self) -> SchemaT:
        return self._load()

    @override
    def __enter__(self) -> SchemaT:
        if self._instance is None:
            self._original = self._open()
            self._instance = replace(self._original)
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

        if exc_type is not None or exc_value is not None:
            self._instance = None

        if self._instance is None or self._instance == self._original:
            self._drop()
        else:
            self._save(self._instance)

        self._pipeline = None
        self._instance = None
        self._original = None
