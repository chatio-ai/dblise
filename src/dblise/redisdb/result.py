
from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client

from .common import Redis


type Invoke[ValueT] = Callable[[Redis], Awaitable[ValueT]]


# pylint: disable=too-few-public-methods
class RedisEngine:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db
        self._op_queue: list[Invoke[object] | None] = []

    @property
    def client(self) -> Redis:
        return self._redis_db

    def submit(self, op: Invoke[object]) -> None:
        self._op_queue.append(op)

    def commit(self) -> None:
        for op in self._op_queue:
            if op is not None:
                op(self._redis_db)
        self._op_queue.clear()


# pylint: disable=too-few-public-methods
class RedisResult[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        engine: RedisEngine,
        invoke: Callable[[Redis], Awaitable[RawValueT]],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._engine = engine
        self._invoke = invoke
        self._decode = decode

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke(self._engine.client))

    def __await__(self) -> Generator[None, None, ValueT]:
        if isinstance(self._invoke, client.Pipeline):
            raise TypeError
        return self._resolve().__await__()

    @staticmethod
    def same[RawValueT](
            engine: RedisEngine, invoke: Invoke[RawValueT]) -> RedisResult[RawValueT]:
        return RedisResult(engine, invoke, lambda value: value)

    @staticmethod
    def void(engine: RedisEngine, invoke: Invoke[object]) -> RedisResult[None]:
        return RedisResult(engine, invoke, lambda _: None)

    @staticmethod
    def pure[RawValueT](
            engine: RedisEngine, invoke: Invoke[RawValueT], value: ValueT) -> RedisResult[ValueT]:
        return RedisResult(engine, invoke, lambda _: value)
