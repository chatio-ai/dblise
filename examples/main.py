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


async def main() -> None:
    facade = RedisFacade()
    schema = facade.schema('test', Tests)

    await schema.test.assign(Test('hello'))
    print(await schema.test.value())

    async with facade.pipeline(schema.test) as test:
        await test.value()
        await test.assign(Test('world'))

    print(await schema.test.value())


if __name__ == '__main__':
    asyncio.run(main())
