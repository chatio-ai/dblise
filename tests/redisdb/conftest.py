
from collections.abc import AsyncGenerator

import typing

import pytest

from redis.asyncio import client as redis

from dblise import Facade
from dblise.redisdb.common import Redis
from dblise.redisdb import RedisFacade


@pytest.fixture(scope='module', params=[False, True])
def transaction(request: pytest.FixtureRequest) -> bool:
    return typing.cast(bool, request.param)


@pytest.fixture(params=[False, True], name='client')
async def _client(request: pytest.FixtureRequest) -> AsyncGenerator[Redis]:
    max_connections = 1 if request.param else None
    async with redis.Redis(max_connections=max_connections, decode_responses=True) as redis_db:
        yield redis_db


@pytest.fixture
async def facade(client: Redis) -> Facade:
    return RedisFacade(redis_db=client)


@pytest.fixture(name='other_client')
async def _other_client() -> AsyncGenerator[Redis]:
    async with redis.Redis(decode_responses=True) as redis_db:
        yield redis_db


@pytest.fixture
async def other_facade(other_client: Redis) -> Facade:
    return RedisFacade(redis_db=other_client)
