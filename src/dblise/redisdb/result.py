
from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client


# pylint: disable=too-few-public-methods
class RedisResult[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        invoke: Awaitable[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._invoke = invoke
        self._decode = decode

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke)

    def __await__(self) -> Generator[None, None, ValueT]:
        if isinstance(self._invoke, client.Pipeline):
            raise TypeError
        return self._resolve().__await__()

    @staticmethod
    def same[RawValueT](invoke: Awaitable[RawValueT]) -> RedisResult[RawValueT]:
        return RedisResult(invoke, lambda value: value)

    @staticmethod
    def void(invoke: Awaitable[object]) -> RedisResult[None]:
        return RedisResult(invoke, lambda _: None)

    @staticmethod
    def pure[RawValueT](invoke: Awaitable[RawValueT], value: ValueT) -> RedisResult[ValueT]:
        return RedisResult(invoke, lambda _: value)
