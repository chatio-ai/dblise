
from collections.abc import Iterable
from collections.abc import Callable
from collections.abc import Awaitable
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from typing import override

from redis.exceptions import WatchError
from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Schema
from dblise.schemas import Entity
from dblise.schemas import Record
from dblise.schemas import Lookup
from dblise.schemas import Scores
from dblise.schemas import Stream
from dblise import Facade

from dblise.helpers import entities

from .common import Redis
from .result import RedisResult
from .codecs import RedisCodecs
from .lookup import RedisLookup
from .record import RedisRecord
from .scores import RedisScores
from .stream import RedisStream


class RedisFacade(Facade):

    def __init__(
        self,
        redis_db: Redis,
        n_digits: int | None = None,
    ) -> None:
        self._redis_db = redis_db
        self._n_digits = n_digits

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
    def exists(self, *objs: Entity | Schema) -> Awaitable[bool]:
        keys = [_.handle for _ in entities(*objs)]
        if not keys:
            return RedisResult.pure(self._redis_db, value=False)
        return RedisResult(self._redis_db.exists(*keys), bool)

    @override
    def delete(self, *objs: Entity | Schema) -> Awaitable[bool]:
        keys = [_.handle for _ in entities(*objs)]
        if not keys:
            return RedisResult.pure(self._redis_db, value=False)
        return RedisResult(self._redis_db.unlink(*keys), bool)

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def pipeline[*ObjectTs](
            self, *objs: *ObjectTs, transaction: bool = True) -> AsyncGenerator[tuple[*ObjectTs]]:
        if isinstance(self._redis_db, client.Pipeline):
            raise TypeError
        async with self._redis_db.pipeline(transaction=transaction) as pipeline:
            facade = type(self)(redis_db=pipeline, n_digits=self._n_digits)
            yield facade.rebinds(*objs)
            await pipeline.execute()

    @override
    async def atomic[ValueT, *ObjectTs](
        self,
        read_fn: Callable[[*ObjectTs], Awaitable[ValueT]],
        write_fn: Callable[[ValueT, *ObjectTs], None],
        *objs: *ObjectTs,
        watches: Iterable[Entity] | None = None,
    ) -> None:
        if isinstance(self._redis_db, client.Pipeline):
            raise TypeError
        if watches is None:
            watches = entities(*objs)
        keys = [_.handle for _ in watches]
        if not keys:
            raise ValueError
        while True:
            try:
                async with self._redis_db.pipeline() as pipeline:
                    facade = type(self)(redis_db=pipeline, n_digits=self._n_digits)
                    objs_ = facade.rebinds(*objs)
                    await pipeline.watch(*keys)
                    data = await read_fn(*objs_)
                    pipeline.multi()
                    write_fn(data, *objs_)
                    await pipeline.execute()
            except WatchError:
                continue
            return
