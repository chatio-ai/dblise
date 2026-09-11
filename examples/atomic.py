#!/usr/bin/env python

import asyncio

from dataclasses import dataclass

from redis.asyncio import Redis, ConnectionPool

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Stream
from dblise.schemas import Schema

from dblise import Facade
from dblise.redisdb import RedisFacade


@dataclass
class Counter(Fields):
    count: int
    note: str | None = None


@dataclass
class Event(Fields):
    what: str


@dataclass(frozen=True)
class Ledger(Schema):
    left: Record[Counter]
    right: Record[Counter]
    log: Stream[Event]


def _facade() -> Facade:
    pool = ConnectionPool(host='localhost', port=6379, db=0, decode_responses=True,
                          max_connections=1)
    return RedisFacade(redis_db=Redis(connection_pool=pool, decode_responses=True))


async def main() -> None:
    facade = _facade()
    ledger = facade.schema('example:atomic', Ledger)
    await facade.delete(ledger)

    # conditional pipe building: awaited reads run at once, un-awaited writes are queued
    await ledger.left.assign(Counter(1))
    await ledger.right.assign(Counter(0, note='x'))

    async def transfer(left: Record[Counter], right: Record[Counter], log: Stream[Event]) -> int:
        lhs = await left.value()
        if lhs.count > 0:
            left.assign(Counter(lhs.count - 1))
            log.append(Event('debit'))
        rhs = await right.value()
        if rhs.count == 0:
            right.assign(Counter(rhs.count + 1))      # drops optional note -> HDEL
            log.append(Event('credit'))
        return lhs.count + rhs.count

    total = await facade.atomic(transfer, ledger.left, ledger.right, ledger.log)
    assert total == 1
    assert await ledger.left.value() == Counter(0)
    assert await ledger.right.value() == Counter(1, note=None)
    assert [e.what for e in await ledger.log.values()] == ['debit', 'credit']

    # retry on contention: first attempt sees a concurrent writer on a watched key
    other = RedisFacade(Redis(host='localhost', port=6379, db=0, decode_responses=True))
    attempts: list[int] = []

    async def bump(left: Record[Counter]) -> None:
        value = await left.value()
        attempts.append(value.count)
        if len(attempts) == 1:
            await other.record(ledger.left.handle, Counter).assign(Counter(10))
        left.assign(Counter(value.count + 1))
        assert (await left.value()).count != value.count + 1   # queued write is never visible

    await facade.atomic(bump, ledger.left)
    assert attempts == [0, 10], attempts
    assert await ledger.left.value() == Counter(11)

    # result awaited inside a plain pipeline is refused; deferred ops flush at exit
    async with facade.pipeline(ledger.left, ledger.right) as (left, right):
        left.value()
        left.assign(Counter(5))
        try:
            await right.value()
        except TypeError:
            pass
        else:
            raise AssertionError
    assert await ledger.left.value() == Counter(5)

    # modify() keeps working on the same broker machinery
    async with ledger.right.modify() as right_:
        right_.count += 41
    assert await ledger.right.value() == Counter(42)

    await facade.delete(ledger)


if __name__ == '__main__':
    asyncio.run(main())
