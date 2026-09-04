#!/usr/bin/env python

# ruff: noqa: T201

import asyncio

from dataclasses import dataclass

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Schema

from dblise.redisdb import RedisFacade


@dataclass
class Test(Fields):
    data: str


@dataclass(frozen=True)
class Tests(Schema):
    test: Record[Test]
    test1: Record[Test]
    test2: Record[Test]


async def main() -> None:
    facade = RedisFacade()
    schema = facade.schema('test', Tests)

    await schema.test.delete()
    assert await schema.test.value() == Test('')
    await schema.test.assign(Test('test'))
    assert await schema.test.value() == Test('test')

    async with facade.pipeline(schema.test) as (test,):
        test.value()
        test.assign(Test('hello'))

    assert await schema.test.value() == Test('hello')

    async with facade.pipeline(schema) as (schema_,):
        schema_.test.value()
        schema_.test.assign(Test('world'))

    assert await schema.test.value() == Test('world')

    async with facade.pipeline(schema.test1, schema.test2) as (test1, test2):
        test1.assign(Test('hello'))
        test2.assign(Test('world'))

    assert await schema.test1.value() == Test('hello')
    assert await schema.test2.value() == Test('world')


if __name__ == '__main__':
    asyncio.run(main())
