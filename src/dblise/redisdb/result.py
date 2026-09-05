
from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client

from .common import Redis


def _asis[ValueT](value: ValueT) -> ValueT:
    return value


def _void(_value: object) -> None:
    return None


class Value[ValueT](Awaitable[ValueT]):
    def __init__(
        self,
        redis_db: Redis,
        value: ValueT,
    ) -> None:
        self._redis_db = redis_db
        self._value = value

    def __await__(self) -> Generator[None, None, ValueT]:
        if isinstance(self._redis_db, client.Pipeline):
            raise TypeError
        return self._value
        yield


# pylint: disable=too-few-public-methods
class Result[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        redis_db: Redis,
        invoke: Awaitable[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._redis_db = redis_db
        self._invoke = invoke
        self._decode = decode

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke)

    def __await__(self) -> Generator[None, None, ValueT]:
        if isinstance(self._redis_db, client.Pipeline):
            raise TypeError
        return self._resolve().__await__()


class Results:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db

    def conv[RawValueT, ValueT](
        self,
        invoke: Awaitable[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> Result[ValueT]:
        return Result(self._redis_db, invoke, decode)

    def void(self, invoke: Awaitable[object]) -> Result[None]:
        return Result(self._redis_db, invoke, _void)

    def asis[ValueT](self, invoke: Awaitable[ValueT]) -> Result[ValueT]:
        return Result(self._redis_db, invoke, _asis)

    def just[ValueT](self, value: ValueT) -> Value[ValueT]:
        return Value(self._redis_db, value)
