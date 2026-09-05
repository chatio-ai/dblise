
from collections.abc import Awaitable
from typing import override

from dblise.schemas import Entity

from .common import Redis
from .result import Results


class RedisEntity(Entity):

    def __init__(self, redis_db: Redis, key_path: str) -> None:
        self._redis_db = redis_db
        self._key_path = key_path
        self._results = Results(redis_db)

    @property
    @override
    def handle(self) -> str:
        return self._key_path

    @override
    def exists(self) -> Awaitable[bool]:
        return self._results.conv(self._redis_db.exists(self._key_path), bool)

    @override
    def delete(self) -> Awaitable[bool]:
        return self._results.conv(self._redis_db.unlink(self._key_path), bool)
