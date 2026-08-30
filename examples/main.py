#!/usr/bin/env python

# ruff: noqa: T201

import asyncio

from dataclasses import dataclass

from redis.asyncio.client import Redis

from dblise.schemas import Fields
from dblise.schemas import Record
from dblise.schemas import Schema

from dblise import Facade
from dblise.redisdb import RedisFacade


@dataclass
class Test(Fields):
    data: str


@dataclass(frozen=True)
class Tests(Schema):
    test: Record[Test]


def _facade() -> Facade:
    return RedisFacade(Redis(host='localhost', port=6379, db=0, decode_responses=True))


async def main() -> None:
    facade = _facade()
    schema = facade.schema('test', Tests)

    await schema.test.assign(Test('hello'))
    print(await schema.test.value())

    async with facade.pipeline() as pipe:
        await pipe.rebind(schema.test).value()
        await pipe.rebind(schema.test).assign(Test('world'))

    print(await schema.test.value())


if __name__ == '__main__':
    asyncio.run(main())
