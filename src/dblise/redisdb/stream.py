
from collections.abc import Awaitable
from collections.abc import Sequence
from collections.abc import Callable

from typing import override

from dblise.schemas import Fields
from dblise.schemas import Stream

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity


class RedisStream[FieldsT: Fields](RedisEntity, Stream[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts: RedisCodecs[FieldsT] = converts

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    @override
    async def len(self) -> int:
        return await self._redis_db.xlen(self._key_path)

    async def _range[ValueT](
        self,
        min_id: str | None = None,
        max_id: str | None = None,
        count: int | None = None,
        *,
        reverse: bool = False,
        convert: Callable[[str, FieldsT], ValueT],
    ) -> Sequence[ValueT]:
        if min_id is None:
            min_id = '-'
        if max_id is None:
            max_id = '+'
        if reverse:
            min_id, max_id = max_id, min_id

        xrange = self._redis_db.xrevrange if reverse else self._redis_db.xrange
        result = await xrange(self._key_path, min_id, max_id, count=count)
        return [convert(k, self._converts.deserialize(v)) for k, v in result]

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
    async def append(self, value: FieldsT, entry_id: str = '*') -> str:
        _ = await self._redis_db.xadd(
                self._key_path, self._converts.serialize(value), id=entry_id)
        assert isinstance(_, str)
        return _

    @override
    async def remove(self, entry_id: str) -> bool:
        return bool(await self._redis_db.xdel(self._key_path, entry_id))
