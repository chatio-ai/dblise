
from collections.abc import Iterator

from typing import override

from dblise.schemas import Schema
from dblise.schemas import Stream

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisStream[SchemaT: Schema](RedisEntity, Stream[SchemaT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[SchemaT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[SchemaT] = converts

    @override
    def __len__(self) -> int:
        return self._redis_db.xlen(self._key_path)

    @override
    def __iter__(self) -> Iterator[SchemaT]:
        return self.values()

    @override
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Iterator[SchemaT]:
        for _, value in self.items(min_id, max_id, count, reverse=reverse):
            yield value

    @override
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Iterator[tuple[str, SchemaT]]:
        xrange = self._redis_db.xrevrange if reverse else self._redis_db.xrange

        if min_id is None:
            min_id = '+' if reverse else '-'
        if max_id is None:
            max_id = '-' if reverse else '+'

        for key, mapping in xrange(self._key_path, min_id, max_id, count=count):
            yield key, self._converts.deserialize(mapping)

    @override
    def append(self, instance: SchemaT, entry_id: str = '*') -> None:
        self._redis_db.xadd(self._key_path, self._converts.serialize(instance), id=entry_id)

    @override
    def remove(self, entry_id: str) -> bool:
        return bool(self._redis_db.xdel(self._key_path, entry_id))
