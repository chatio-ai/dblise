
import math

from collections.abc import Awaitable
from collections.abc import Sequence

from typing import override

from dblise.schemas import Scores

from .entity import RedisEntity


class RedisScores(RedisEntity, Scores):

    @property
    @override
    def fields(self) -> None:
        return None

    @override
    def values(self, *, reverse: bool = False) -> Awaitable[Sequence[str]]:
        return self._redis_db.zrange(self._key_path, 0, -1, desc=reverse)

    @override
    def scores(self, *, reverse: bool = False) -> Awaitable[Sequence[tuple[str, float]]]:
        return self._redis_db.zrange(self._key_path, 0, -1, desc=reverse, withscores=True)

    @override
    async def index(self, key: str, *, reverse: bool = False) -> int | None:
        zrank = self._redis_db.zrevrank if reverse else self._redis_db.zrank
        return await zrank(self._key_path, key)

    @override
    async def score(self, key: str) -> float | None:
        return await self._redis_db.zscore(self._key_path, key)

    @override
    async def count(self) -> int:
        return await self._redis_db.zcount(self._key_path, -math.inf, math.inf)

    @override
    async def len(self) -> int:
        return await self._redis_db.zcard(self._key_path)

    @override
    async def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> bool:
        return bool(await self._redis_db.zadd(self._key_path, {key: score}, xx=xx, nx=nx))

    @override
    async def remove(self, key: str) -> bool:
        return bool(await self._redis_db.zrem(self._key_path, key))
