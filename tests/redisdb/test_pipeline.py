
from collections.abc import AsyncGenerator

from dataclasses import dataclass
from uuid import uuid4

import pytest

from redis.asyncio import client

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Lookup
from dblise.schemas import Schema

from dblise.helpers import entities

from dblise import Facade

pytestmark = pytest.mark.anyio


@dataclass
class Item(Fields):
    data: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Items(Schema):
    test: Record[Item]
    test1: Record[Item]
    test2: Record[Item]
    lookup: Lookup[Item]


@dataclass(frozen=True)
class Empty(Schema):
    pass


@pytest.fixture(name='schema')
async def _schema(facade: Facade) -> AsyncGenerator[Items]:
    schema = facade.schema(f'test:main:{uuid4().hex}', Items)
    for entity in entities(schema):
        await entity.delete()
    yield schema
    for entity in entities(schema):
        await entity.delete()


async def test_record_direct(schema: Items) -> None:
    await schema.test.delete()
    assert await schema.test.value() == Item()
    await schema.test.assign(Item('test'))
    assert await schema.test.value() == Item('test')
    schema.test.assign(Item('lazy'))
    assert await schema.test.value() == Item('test')


async def test_record_atomic(schema: Items, monkeypatch: pytest.MonkeyPatch) -> None:
    await schema.test.assign(Item('old', note='note'))

    def _raise(*args: object, **kwargs: object) -> None:
        raise NotImplementedError

    with monkeypatch.context() as patch:
        patch.setattr(client.Redis, 'hdel', _raise)
        with pytest.raises(NotImplementedError):
            await schema.test.assign(Item('new'))

    assert await schema.test.value() == Item('old', 'note')


async def test_record_nullify(schema: Items) -> None:
    await schema.test.assign(Item('data', 'note'))
    await schema.test.assign(Item())
    assert await schema.test.value() == Item()
    assert not await schema.test.exists()


async def test_schema_exists(facade: Facade, schema: Items) -> None:
    await schema.test.assign(Item('test'))
    assert await facade.exists(schema)
    assert not await facade.exists(Empty())
    assert not await facade.delete(Empty())


async def test_pipeline_entity(facade: Facade, schema: Items, *, transaction: bool) -> None:
    async with facade.pipeline(schema.test, transaction=transaction) as (test,):
        test.value()
        test.delete()
        test.assign(Item('hello'))
    assert await schema.test.value() == Item('hello')


async def test_pipeline_schema(facade: Facade, schema: Items, *, transaction: bool) -> None:
    async with facade.pipeline(schema, transaction=transaction) as (schema_,):
        schema_.test.value()
        schema_.test.assign(Item('world'))
    assert await schema.test.value() == Item('world')


async def test_pipeline_entities(facade: Facade, schema: Items, *, transaction: bool) -> None:
    async with facade.pipeline(
            schema.test1, schema.test2, transaction=transaction) as (test1, test2):
        test1.assign(Item('hello'))
        test2.assign(Item('world'))
    assert await schema.test1.value() == Item('hello')
    assert await schema.test2.value() == Item('world')


async def test_results_caching(schema: Items) -> None:
    await schema.test1.assign(Item('hello'))

    before = schema.test1.value()
    exists = schema.test2.exists()
    assign = schema.test2.assign(Item('world'))
    after = schema.test2.value()
    delete = schema.test2.delete()

    assert await before == Item('hello')
    assert not await exists
    await assign
    assert not await exists

    assert await after == Item('world')
    assert await delete
    assert await after == Item('world')
    assert await delete


async def test_pipeline_results(facade: Facade, schema: Items, *, transaction: bool) -> None:
    await schema.test1.assign(Item('hello'))
    async with facade.pipeline(schema, transaction=transaction) as (schema_,):
        before = schema_.test1.value()
        exists = schema_.test2.exists()
        assign = schema_.test2.assign(Item('world'))
        after = schema_.test2.value()
        delete = schema_.test2.delete()

    assert await before == Item('hello')
    assert not await exists
    await assign
    assert not await exists

    assert await after == Item('world')
    assert await delete
    assert await after == Item('world')
    assert await delete


async def test_lookup_record(schema: Items) -> None:
    await schema.lookup.lookup('key').assign(Item('found'))
    assert await schema.lookup.lookup('key').value() == Item('found')
