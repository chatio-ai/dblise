from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

import pytest

from redis.asyncio import client as redis
from redis.exceptions import WatchError

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Stream
from dblise.schemas import Schema

from dblise import Facade
from dblise.redisdb.common import Redis

pytestmark = pytest.mark.anyio


@dataclass
class Counter(Fields):
    count: int
    note: str | None = None


@dataclass
class Nothing(Fields):
    pass


@dataclass
class Event(Fields):
    what: str


@dataclass(frozen=True)
class Ledger(Schema):
    left: Record[Counter]
    right: Record[Counter]
    empty: Record[Nothing]
    log: Stream[Event]


@pytest.fixture(name='ledger')
async def _ledger(facade: Facade) -> AsyncGenerator[Ledger]:
    ledger = facade.schema(f'test:atomic:{uuid4().hex}', Ledger)
    await facade.delete(ledger)
    yield ledger
    await facade.delete(ledger)


async def test_record_assign(ledger: Ledger) -> None:
    await ledger.left.assign(Counter(1))
    assert await ledger.left.value() == Counter(1)
    await ledger.left.assign(Counter(0, note='note'))
    assert await ledger.left.value() == Counter(0, note='note')
    await ledger.left.assign(Counter(1))
    assert await ledger.left.value() == Counter(1)


async def test_empty_assign(facade: Facade, ledger: Ledger, *, transaction: bool) -> None:
    await ledger.empty.assign(Nothing())
    assert await ledger.empty.value() == Nothing()

    async with facade.pipeline(ledger.empty, transaction=transaction) as (empty,):
        empty.assign(Nothing())
    assert await ledger.empty.value() == Nothing()

    async def assign(empty: Record[Nothing]) -> None:
        await empty.value()
        empty.assign(Nothing())

    await facade.atomic(assign, ledger.empty)
    assert await ledger.empty.value() == Nothing()


async def test_atomic_immediate(facade: Facade, ledger: Ledger) -> None:
    async def assign(right: Record[Counter]) -> None:
        await right.assign(Counter(2, note='now'))
        assert await right.value() == Counter(2, note='now')
        await right.assign(Counter(3))
        assert await right.value() == Counter(3)

    await facade.atomic(assign, ledger.right, watches=(ledger.left,))


async def test_atomic_connections(facade: Facade, client: Redis, ledger: Ledger) -> None:
    async def assign(right: Record[Counter]) -> None:
        await right.assign(Counter(2, note='now'))

    await facade.atomic(assign, ledger.right, watches=(ledger.left,))
    assert sum(count for count, _ in client.connection_pool.get_connection_count()) == 1


async def test_atomic_transfer(facade: Facade, ledger: Ledger) -> None:
    await ledger.left.assign(Counter(1))
    await ledger.right.assign(Counter(0))

    async def transfer(left: Record[Counter], right: Record[Counter], log: Stream[Event]) -> int:
        lhs = await left.value()
        if lhs.count > 0:
            left.assign(Counter(lhs.count - 1))
            log.append(Event('debit'))
        rhs = await right.value()
        if rhs.count == 0:
            right.assign(Counter(rhs.count + 1))
            log.append(Event('credit'))
        return lhs.count + rhs.count

    total = await facade.atomic(transfer, ledger.left, ledger.right, ledger.log)
    assert total == 1
    assert await ledger.left.value() == Counter(0)
    assert await ledger.right.value() == Counter(1)
    assert [e.what for e in await ledger.log.values()] == ['debit', 'credit']


async def test_atomic_retries(facade: Facade, other_facade: Facade, ledger: Ledger) -> None:
    reads: list[int] = []

    async def bump(left: Record[Counter]) -> None:
        value = await left.value()
        reads.append(value.count)
        if len(reads) == 1:
            await other_facade.record(ledger.left.handle, Counter).assign(Counter(10))
        left.assign(Counter(value.count + 1))
        assert (await left.value()).count != value.count + 1

    await facade.atomic(bump, ledger.left)
    assert reads == [0, 10]
    assert await ledger.left.value() == Counter(11)


async def test_atomic_atomic(
        facade: Facade, ledger: Ledger, monkeypatch: pytest.MonkeyPatch) -> None:
    await ledger.right.assign(Counter(1, note='note'))

    def _raise(*args: object, **kwargs: object) -> None:
        raise NotImplementedError

    async def assign(right: Record[Counter]) -> None:
        assert await right.value() == Counter(1, note='note')
        right.assign(Counter(2))

    with monkeypatch.context() as patch:
        patch.setattr(redis.Pipeline, 'hdel', _raise)
        with pytest.raises(RuntimeError):
            await facade.atomic(assign, ledger.right)

    assert await ledger.right.value() == Counter(1, note='note')


async def test_atomic_connect(
        facade: Facade, client: Redis, other_client: Redis, ledger: Ledger) -> None:
    drops: list[int] = []

    client_id = await client.client_id()

    async def drop(right: Record[Counter]) -> None:
        value = await right.value()
        drops.append(value.count)
        if len(drops) == 1:
            await other_client.client_kill_filter(_id=client_id)
            await right.value()
        right.assign(Counter(value.count + 1))

    await facade.atomic(drop, ledger.right)
    assert drops == [0, 0]
    assert await ledger.right.value() == Counter(1)


async def test_pipeline_refuse(facade: Facade, ledger: Ledger, *, transaction: bool) -> None:
    async with facade.pipeline(
            ledger.left, ledger.right, transaction=transaction) as (left, right):
        left.value()
        left.assign(Counter(5, note='extra'))
        right.assign(Counter(5, note='base'))

        with pytest.raises(TypeError):
            await right.assign(Counter(0))

    assert await ledger.left.value() == Counter(5, 'extra')
    assert await ledger.right.value() == Counter(5, 'base')


async def test_pipeline_nested(facade: Facade, ledger: Ledger, *, transaction: bool) -> None:
    async with facade.pipeline(ledger.empty, transaction=transaction) as (empty,):
        empty.assign(Nothing())
        async with empty.modify():
            pass


async def test_record_modify(ledger: Ledger) -> None:
    await ledger.right.assign(Counter(1, note='main'))
    async with ledger.right.modify() as right_:
        right_.count += 41
        right_.note = None
    assert await ledger.right.value() == Counter(42)


async def test_modify_conflict(ledger: Ledger, other_facade: Facade) -> None:
    await ledger.right.assign(Counter(1, note='old'))

    async def modify() -> None:
        async with ledger.right.modify() as value:
            value.count = 2
            await other_facade.record(ledger.right.handle, Counter).assign(
                Counter(3, note='new'))

    with pytest.raises(WatchError):
        await modify()

    assert await ledger.right.value() == Counter(3, note='new')
