
from typing import override

from dblise.schemas import Domain

from .common import Redis
from .entity import RedisEntity


class RedisDomain(RedisEntity, Domain):

    def __init__(self, redis_db: Redis, key_path: str) -> None:
        super().__init__(redis_db, key_path)
        self._key_glob = f'{key_path}:*'

    @override
    async def exists(self) -> bool:
        async for _ in self._redis_db.scan_iter(self._key_glob):
            return True
        return False

    @override
    async def delete(self) -> bool:
        keys = [_ async for _ in self._redis_db.scan_iter(self._key_glob)]
        if keys:
            await self._redis_db.unlink(*keys)
        return bool(keys)
