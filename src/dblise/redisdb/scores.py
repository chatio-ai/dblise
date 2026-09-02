
import math

from collections.abc import AsyncIterator

from typing import override

from dblise.schemas import Result
from dblise.schemas import Scores

from .entity import RedisEntity


class RedisScores(RedisEntity, Scores):

    @property
    @override
    def fields(self) -> None:
        return None

    @override
    def __aiter__(self) -> AsyncIterator[str]:
        return self.values()

    @override
    # pylint: disable=invalid-overridden-method
    async def values(self, *, reverse: bool = False) -> AsyncIterator[str]:
        for _ in await self._redis_db.zrange(self._key_path, 0, -1, desc=reverse):
            yield _

    @override
    # pylint: disable=invalid-overridden-method
    async def scores(self, *, reverse: bool = False) -> AsyncIterator[tuple[str, float]]:
        for _ in await self._redis_db.zrange(self._key_path, 0, -1, desc=reverse, withscores=True):
            yield _

    @override
    def index(self, key: str, *, reverse: bool = False) -> Result[int | None]:
        zrank = self._redis_db.zrevrank if reverse else self._redis_db.zrank
        return Result(zrank(self._key_path, key), Result.ASIS)

    @override
    def score(self, key: str) -> Result[float | None]:
        return Result(self._redis_db.zscore(self._key_path, key), Result.ASIS)

    @override
    def count(self) -> Result[int]:
        return Result(self._redis_db.zcount(self._key_path, -math.inf, math.inf), Result.ASIS)

    @override
    def len(self) -> Result[int]:
        return Result(self._redis_db.zcard(self._key_path), Result.ASIS)

    @override
    def insert(
            self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> Result[bool]:
        return Result(self._redis_db.zadd(self._key_path, {key: score}, xx=xx, nx=nx), bool)

    @override
    def remove(self, key: str) -> Result[bool]:
        return Result(self._redis_db.zrem(self._key_path, key), bool)
