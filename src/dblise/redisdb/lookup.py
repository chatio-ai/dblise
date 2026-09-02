
from typing import override

from dblise.schemas import Fields
from dblise.schemas import Result
from dblise.schemas import Record
from dblise.schemas import Lookup

from .common import Redis
from .codecs import RedisCodecs
from .entity import RedisEntity
from .record import RedisRecord


class RedisLookup[FieldsT: Fields](RedisEntity, Lookup[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts = converts
        self._key_glob = f'{key_path}:*'

    @property
    @override
    def fields(self) -> type[FieldsT]:
        return self._converts.data_cls

    @override
    def lookup(self, key: str) -> Record[FieldsT]:
        return RedisRecord(self._redis_db, f'{self._key_path}:{key}', self._converts)

    async def _exists(self) -> bool:
        async for _ in self._redis_db.scan_iter(self._key_glob):
            return True
        return False

    @override
    def exists(self) -> Result[bool]:
        raise NotImplementedError

    async def _delete(self) -> bool:
        keys = [_ async for _ in self._redis_db.scan_iter(self._key_glob)]
        if keys:
            await self._redis_db.unlink(*keys)
        return bool(keys)

    @override
    def delete(self) -> Result[bool]:
        raise NotImplementedError
