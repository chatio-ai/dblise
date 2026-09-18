
from collections.abc import AsyncGenerator

import typing

import pytest

from redis.asyncio import Redis

from dblise.redisdb import RedisFacade


@pytest.fixture(scope='module', params=[False, True])
def transaction(request: pytest.FixtureRequest) -> bool:
    return typing.cast(bool, request.param)


@pytest.fixture(params=[False, True])
async def facade(request: pytest.FixtureRequest) -> AsyncGenerator[RedisFacade]:
    max_connections = 1 if request.param else None
    async with Redis(max_connections=max_connections, decode_responses=True) as redis_db:
        yield RedisFacade(redis_db=redis_db)


@pytest.fixture
async def other_facade() -> AsyncGenerator[RedisFacade]:
    async with Redis(decode_responses=True) as redis_db:
        yield RedisFacade(redis_db=redis_db)
