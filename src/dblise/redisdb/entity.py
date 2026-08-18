
from typing import override

from dblise.schemas import Entity

from .common import Redis


class RedisEntity(Entity):

    def __init__(self, redis_db: Redis, key_path: str) -> None:
        self._redis_db = redis_db
        self._key_path = key_path

    @override
    def exists(self) -> bool:
        return bool(self._redis_db.exists(self._key_path))

    @override
    def delete(self) -> bool:
        return bool(self._redis_db.unlink(self._key_path))
