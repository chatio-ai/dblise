
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
from .result import RedisBroker
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
        self._broker = RedisBroker(redis_db)
        self._n_digits = n_digits

    @property
    def broker(self) -> RedisBroker:
        return self._broker

    def _codec[FieldsT: Fields](self, fields: type[FieldsT]) -> RedisCodecs[FieldsT]:
        return RedisCodecs(fields, self._n_digits)

    @override
    def record[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Record[FieldsT]:
        return RedisRecord(self._broker, handle, self._codec(fields))

    @override
    def lookup[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Lookup[FieldsT]:
        return RedisLookup(self._broker, handle, self._codec(fields))

    @override
    def scores(self, handle: str) -> Scores:
        return RedisScores(self._broker, handle)

    @override
    def stream[FieldsT: Fields](self, handle: str, fields: type[FieldsT]) -> Stream[FieldsT]:
        return RedisStream(self._broker, handle, self._codec(fields))

    @override
    def handle(self, parent: str, child: str) -> str:
        return f'{parent}:{child}'

    @override
    def exists(self, *objs: Entity | Schema) -> Awaitable[bool]:
        keys = [_.handle for _ in entities(*objs)]
        if not keys:
            return self._broker.pure(value=False)
        return self._broker.cast(lambda redis: redis.exists(*keys), bool)

    @override
    def delete(self, *objs: Entity | Schema) -> Awaitable[bool]:
        keys = [_.handle for _ in entities(*objs)]
        if not keys:
            return self._broker.pure(value=False)
        return self._broker.cast(lambda redis: redis.unlink(*keys), bool)

    @override
    @asynccontextmanager
    # pylint: disable=invalid-overridden-method
    async def pipeline[*ObjectTs](
            self, *objs: *ObjectTs, transaction: bool = True) -> AsyncGenerator[tuple[*ObjectTs]]:
        if isinstance(self._broker.client, client.Pipeline):
            raise TypeError
        async with self._broker.client.pipeline(transaction=transaction) as pipeline:
            facade = type(self)(redis_db=pipeline, n_digits=self._n_digits)
            yield facade.rebinds(*objs)
            await facade.broker.execute()

    @override
    async def atomic[ValueT, *ObjectTs](
        self,
        func: Callable[[*ObjectTs], Awaitable[ValueT]],
        *objs: *ObjectTs,
        watches: Iterable[Entity] | None = None,
    ) -> ValueT:
        if isinstance(self._broker.client, client.Pipeline):
            raise TypeError
        if watches is None:
            watches = entities(*objs)
        keys = [_.handle for _ in watches]
        if not keys:
            raise ValueError
        while True:
            try:
                async with self._broker.client.pipeline() as pipeline:
                    facade = type(self)(redis_db=pipeline, n_digits=self._n_digits)
                    await facade.broker.watch(*keys)
                    value = await func(*facade.rebinds(*objs))
                    await facade.broker.execute()
            except WatchError:
                continue
            return value
