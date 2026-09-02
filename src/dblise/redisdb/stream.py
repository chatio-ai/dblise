
from collections.abc import Awaitable
from collections.abc import Sequence
from collections.abc import Callable

from typing import override

from dblise.schemas import Fields
from dblise.schemas import Stream

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity
from .result import RedisResult


class RedisStream[FieldsT: Fields](RedisEntity, Stream[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    @override
    def len(self) -> Awaitable[int]:
        return RedisResult.same(self._redis_db.xlen(self._key_path))

    def _range[ValueT](
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
        convert: Callable[[str, FieldsT], ValueT],
    ) -> Awaitable[Sequence[ValueT]]:
        if min_id is None:
            min_id = '-'
        if max_id is None:
            max_id = '+'
        if reverse:
            min_id, max_id = max_id, min_id

        xrange = self._redis_db.xrevrange if reverse else self._redis_db.xrange
        return RedisResult(
            xrange(self._key_path, min_id, max_id, count=count),
            lambda result: [convert(k, self._converts.deserialize(v)) for k, v in result])

    @override
    def values(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Awaitable[Sequence[FieldsT]]:
        return self._range(min_id, max_id, count, reverse=reverse, convert=lambda _, v: v)

    @override
    def items(
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
    ) -> Awaitable[Sequence[tuple[str, FieldsT]]]:
        return self._range(min_id, max_id, count, reverse=reverse, convert=lambda k, v: (k, v))

    @override
    def append(self, value: FieldsT, entry_id: str = '*') -> Awaitable[str]:
        return RedisResult.same(self._redis_db.xadd(
            self._key_path, self._converts.serialize(value), id=entry_id))

    @override
    def remove(self, entry_id: str) -> Awaitable[bool]:
        return RedisResult(self._redis_db.xdel(self._key_path, entry_id), bool)
