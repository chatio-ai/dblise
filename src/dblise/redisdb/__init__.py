
from collections.abc import Awaitable
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from typing import override
from typing import cast

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Schema
from dblise.schemas import Entity
from dblise.schemas import Record
from dblise.schemas import Lookup
from dblise.schemas import Scores
from dblise.schemas import Stream
from dblise import Facade

from dblise.helpers.typing import entities

from .common import Redis
from .result import Results
from .codecs import RedisCodecs
from .lookup import RedisLookup
from .record import RedisRecord
from .scores import RedisScores
from .stream import RedisStream


class RedisFacade(Facade):

    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        redis_db: Redis | None = None,
        n_digits: int | None = None,
    ) -> None:
        if redis_db is None:
            redis_db = client.Redis(host=host, port=port, db=0, decode_responses=True)

        self._redis_db = redis_db
        self._n_digits = n_digits
        self._results = Results(redis_db)

    def _codec[FieldsT: Fields](self, fields: type[FieldsT]) -> RedisCodecs[FieldsT]:
        return RedisCodecs(fields, self._n_digits)

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

    @override
    def exists(self, schema: Schema) -> Awaitable[bool]:
        keys = [entity.handle for _, entity in entities(schema)]
        if not keys:
            return self._results.just(value=False)
        return self._results.conv(self._redis_db.exists(*keys), bool)

    @override
    def delete(self, schema: Schema) -> Awaitable[bool]:
        keys = [entity.handle for _, entity in entities(schema)]
        if not keys:
            return self._results.just(value=False)
        return self._results.conv(self._redis_db.unlink(*keys), bool)

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def pipeline[*ObjectTs](self, *objs: *ObjectTs) -> AsyncGenerator[tuple[*ObjectTs]]:
        async with self._redis_db.pipeline() as pipeline:
            facade = type(self)(redis_db=pipeline, n_digits=self._n_digits)

            def _rebind[ObjectT](obj: ObjectT) -> ObjectT:
                if not isinstance(obj, Entity | Schema):
                    raise TypeError(obj)
                return facade.rebind(obj)

            yield cast(tuple[*ObjectTs], tuple(_rebind(obj) for obj in objs))
            await pipeline.execute()
