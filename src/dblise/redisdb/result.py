
from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from redis.asyncio import client

from .common import Redis


type Invoke[_ValueT] = Callable[[Redis], Awaitable[_ValueT]]


class RedisResult[ValueT](Awaitable[ValueT]):
    def __init__[RawValueT](
        self,
        redis_db: Redis,
        invoke: Invoke[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> None:
        self._redis_db = redis_db
        self._invoke = invoke
        self._decode = decode
        self._is_awaited = False

    async def invoke(self) -> object:
        if self._is_awaited:
            return None
        return await self._invoke(self._redis_db)

    async def _resolve(self) -> ValueT:
        return self._decode(await self._invoke(self._redis_db))

    @property
    def _is_batched(self) -> bool:
        if not isinstance(self._redis_db, client.Pipeline):
            return False
        return not self._redis_db.watching or self._redis_db.explicit_transaction

    def __await__(self) -> Generator[None, None, ValueT]:
        self._is_awaited = True
        if self._is_batched:
            raise TypeError
        return self._resolve().__await__()


class RedisBroker:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db
        self._results: list[RedisResult[object]] = []

    @property
    def client(self) -> Redis:
        return self._redis_db

    async def commit(self) -> None:
        results, self._results = self._results, []
        for result in results:
            await result.invoke()

    def cast[RawValueT, ValueT](
        self,
        invoke: Invoke[RawValueT],
        decode: Callable[[RawValueT], ValueT],
    ) -> RedisResult[ValueT]:
        result = RedisResult(self._redis_db, invoke, decode)
        if isinstance(self._redis_db, client.Pipeline):
            self._results.append(result)
        return result

    def same[RawValueT](self, invoke: Invoke[RawValueT]) -> RedisResult[RawValueT]:
        return self.cast(invoke, lambda value: value)

    def void(self, invoke: Invoke[object]) -> RedisResult[None]:
        return self.cast(invoke, lambda _: None)

    def pipe(self, invoke: Invoke[None]) -> RedisResult[None]:
        if isinstance(self._redis_db, client.Pipeline):
            return self.void(invoke)

        async def _pipe(redis: Redis) -> None:
            async with redis.pipeline() as pipeline:
                await invoke(pipeline)
                await pipeline.execute()

        return self.void(_pipe)

    @staticmethod
    async def _value[ValueT](value: ValueT) -> ValueT:
        return value

    def pure[ValueT](self, value: ValueT) -> RedisResult[ValueT]:
        return self.same(lambda _: self._value(value))
