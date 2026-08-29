
from typing import override

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Lookup

from .common import Redis
from .codecs import RedisCodecs
from .domain import RedisDomain
from .record import RedisRecord


class RedisLookup[FieldsT: Fields](RedisDomain, Lookup[FieldsT]):

    def __init__(self, redis_db: Redis, key_path: str, converts: RedisCodecs[FieldsT]) -> None:
        super().__init__(redis_db, key_path)
        self._converts = converts

    @override
    def lookup(self, key: str) -> Record[FieldsT]:
        return RedisRecord(self._redis_db, f'{self._key_path}:{key}', self._converts)
