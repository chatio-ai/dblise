
from typing import override

from redis.asyncio import Redis

from dblise.schemas import Fields
from dblise.schemas import Domain
from dblise.schemas import Record
from dblise.schemas import Lookup
from dblise.schemas import Scores
from dblise.schemas import Stream
from dblise import Facade

from .codecs import RedisCodecs
from .domain import RedisDomain
from .lookup import RedisLookup
from .record import RedisRecord
from .scores import RedisScores
from .stream import RedisStream


class RedisFacade(Facade):

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        n_digits: int | None = None,
    ) -> None:
        self._redis_db = Redis(host=host, port=port, db=0, decode_responses=True)
        self._n_digits = n_digits

    def _codec[FieldsT: Fields](self, fields: type[FieldsT]) -> RedisCodecs[FieldsT]:
        return RedisCodecs(fields, self._n_digits)

    @override
    def domain(self, key_path: str) -> Domain:
        return RedisDomain(self._redis_db, key_path)

    @override
    def record[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Record[FieldsT]:
        return RedisRecord(self._redis_db, handle, self._codec(fields))

    @override
    def lookup[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Lookup[FieldsT]:
        return RedisLookup(self._redis_db, handle, self._codec(fields))

    @override
    def scores(self, handle: str) -> Scores:
        return RedisScores(self._redis_db, handle)

    @override
    def stream[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Stream[FieldsT]:
        return RedisStream(self._redis_db, handle, self._codec(fields))

    @override
    def handle(self, parent: str, child: str) -> str:
        return f'{parent}:{child}'
