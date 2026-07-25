
from typing import override

from redis import Redis

from dblise.schemas import Schema
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

    def _codec[SchemaT: Schema](self, obj_type: type[SchemaT]) -> RedisCodecs[SchemaT]:
        return RedisCodecs(obj_type, self._n_digits)

    @override
    def domain(self, key_path: str) -> Domain:
        return RedisDomain(self._redis_db, key_path)

    @override
    def record[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Record[SchemaT]:
        return RedisRecord(self._redis_db, key_path, self._codec(obj_type))

    @override
    def lookup[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Lookup[SchemaT]:
        return RedisLookup(self._redis_db, key_path, self._codec(obj_type))

    @override
    def scores(self, key_path: str) -> Scores:
        return RedisScores(self._redis_db, key_path)

    @override
    def stream[SchemaT: Schema](self, key_path: str, obj_type: type[SchemaT]) -> Stream[SchemaT]:
        return RedisStream(self._redis_db, key_path, self._codec(obj_type))
