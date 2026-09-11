
from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client

from .common import Redis


# pylint: disable=too-few-public-methods
class RedisEngine:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db

    @property
    def client(self) -> Redis:
        return self._redis_db


# pylint: disable=too-few-public-methods
class RedisResult[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        engine: RedisEngine,
        invoke: Awaitable[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._engine = engine
        self._invoke = invoke
        self._decode = decode

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke)

    def __await__(self) -> Generator[None, None, ValueT]:
        if isinstance(self._invoke, client.Pipeline):
            raise TypeError
        return self._resolve().__await__()

    @staticmethod
    def same[RawValueT](
            engine: RedisEngine, invoke: Awaitable[RawValueT]) -> RedisResult[RawValueT]:
        return RedisResult(engine, invoke, lambda value: value)

    @staticmethod
    def void(engine: RedisEngine, invoke: Awaitable[object]) -> RedisResult[None]:
        return RedisResult(engine, invoke, lambda _: None)

    @staticmethod
    def pure[RawValueT](
            engine: RedisEngine,
            invoke: Awaitable[RawValueT], value: ValueT) -> RedisResult[ValueT]:
        return RedisResult(engine, invoke, lambda _: value)
