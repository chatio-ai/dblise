
from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client

from .common import Redis


type Invoke[_ValueT] = Callable[[Redis], Awaitable[_ValueT]]


class RedisBroker:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db
        self._op_queue: list[Invoke[object] | None] = []

    @property
    def client(self) -> Redis:
        return self._redis_db

    @property
    def is_piped(self) -> bool:
        if not isinstance(self._redis_db, client.Pipeline):
            return False
        return not self._redis_db.watching or self._redis_db.explicit_transaction

    def submit(self, op: Invoke[object]) -> int | None:
        if not isinstance(self._redis_db, client.Pipeline):
            return None
        self._op_queue.append(op)
        return len(self._op_queue) - 1

    def redeem(self, ticket: int | None) -> None:
        if ticket is not None:
            self._op_queue[ticket] = None

    async def commit(self) -> None:
        ops, self._op_queue = self._op_queue, []
        for op in ops:
            if op is not None:
                await op(self._redis_db)


class RedisResult[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        broker: RedisBroker,
        invoke: Invoke[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._broker = broker
        self._invoke = invoke
        self._decode = decode
        self._ticket = broker.submit(invoke)

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke(self._broker.client))

    def __await__(self) -> Generator[None, None, ValueT]:
        self._broker.redeem(self._ticket)
        if self._broker.is_piped:
            raise TypeError
        return self._resolve().__await__()

    @staticmethod
    def same[RawValueT](
            broker: RedisBroker, invoke: Invoke[RawValueT]) -> RedisResult[RawValueT]:
        return RedisResult(broker, invoke, lambda value: value)

    @staticmethod
    def void(broker: RedisBroker, invoke: Invoke[object]) -> RedisResult[None]:
        return RedisResult(broker, invoke, lambda _: None)

    @staticmethod
    async def _value(value: ValueT) -> ValueT:
        return value

    @staticmethod
    def pure(broker: RedisBroker, value: ValueT) -> RedisResult[ValueT]:
        return RedisResult.same(broker, lambda _: RedisResult._value(value))
