
from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Callable

from dataclasses import dataclass

from typing import cast

from redis.asyncio import client

from .common import Redis
from .common import Pipeline


type Invoke[_ValueT] = Callable[[Redis], Awaitable[_ValueT]]
type Settle = Callable[[*tuple[object, ...]], None]


def _is_batched(pipeline: Pipeline) -> bool:
    return not pipeline.watching or pipeline.explicit_transaction


@dataclass(frozen=True)
class _ResultValue[ValueT]:
    value: ValueT


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

        self._result: _ResultValue[ValueT] | None = None
        self._is_awaited = False

    async def submit(self) -> Settle | None:
        if self._is_awaited:
            return None

        await self._invoke(self._redis_db)

        def _settle(*args: object) -> None:
            decode = cast(Callable[[object], ValueT], self._decode)
            self._result = _ResultValue(decode(args[0] if args else None))

        return _settle

    async def _resolve(self) -> ValueT:
        if self._result is None:
            self._result = _ResultValue(self._decode(await self._invoke(self._redis_db)))

        return self._result.value

    def __await__(self) -> Generator[None, None, ValueT]:
        if self._result is None:
            self._is_awaited = True
            if isinstance(self._redis_db, client.Pipeline) and _is_batched(self._redis_db):
                raise TypeError
        return self._resolve().__await__()


class RedisBroker:
    def __init__(self, redis_db: Redis) -> None:
        self._redis_db = redis_db
        self._results: list[RedisResult[object]] = []

    @property
    def client(self) -> Redis:
        return self._redis_db

    async def watch(self, *keys: str) -> None:
        if isinstance(self._redis_db, client.Pipeline):
            await self._redis_db.watch(*keys)

    async def execute(self) -> None:
        if not isinstance(self._redis_db, client.Pipeline):
            raise TypeError

        if not _is_batched(self._redis_db):
            self._redis_db.multi()

        results, self._results = self._results, []
        settles: list[tuple[Settle, int, int]] = []
        for result in results:
            length = len(self._redis_db.command_stack)
            settle = await result.submit()
            if settle is not None:
                settles.append((settle, length, len(self._redis_db.command_stack)))

        replies = await self._redis_db.execute()
        for settle, start, end in settles:
            settle(*replies[start:end])

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

    def bulk(self, invoke: Invoke[None]) -> RedisResult[None]:
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
