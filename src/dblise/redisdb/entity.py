
from collections.abc import Awaitable
from typing import override

from dblise.schemas import Entity

from .result import RedisResult
from .result import RedisEngine


class RedisEntity(Entity):

    def __init__(self, engine: RedisEngine, key_path: str) -> None:
        self._engine = engine
        self._key_path = key_path

    @property
    @override
    def handle(self) -> str:
        return self._key_path

    @override
    def exists(self) -> Awaitable[bool]:
        return RedisResult(self._engine, lambda redis: redis.exists(self._key_path), bool)

    @override
    def delete(self) -> Awaitable[bool]:
        return RedisResult(self._engine, lambda redis: redis.unlink(self._key_path), bool)
