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
    print(await schema.test.value())

    async with facade.pipeline(schema.test) as (test,):
        test.value()
        await test.assign(Test('hello'))

    print(await schema.test.value())

    async with facade.pipeline(schema) as (schema_,):
        schema_.test.value()
        await schema_.test.assign(Test('world'))

    print(await schema.test.value())

    async with facade.pipeline(schema.test1, schema.test2) as (test1, test2):
        await test1.assign(Test('hello'))
        await test2.assign(Test('world'))

    print(await schema.test1.value())
    print(await schema.test2.value())


if __name__ == '__main__':
    asyncio.run(main())
