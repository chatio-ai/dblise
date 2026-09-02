
from collections.abc import Awaitable
from typing import override

from dblise.schemas import Entity

from .common import Redis
from .result import RedisResult


class RedisEntity(Entity):

    def __init__(self, redis_db: Redis, key_path: str) -> None:
        self._redis_db = redis_db
        self._key_path = key_path

    @property
    @override
    def handle(self) -> str:
        return self._key_path

    @override
    def exists(self) -> Awaitable[bool]:
        return RedisResult(self._redis_db.exists(self._key_path), bool)

    @override
    def delete(self) -> Awaitable[bool]:
        return RedisResult(self._redis_db.unlink(self._key_path), bool)
