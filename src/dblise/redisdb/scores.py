
import math

from collections.abc import Awaitable
from collections.abc import Iterator
from typing import override

from dblise.schemas import Scores

from .entity import RedisEntity


class RedisScores(RedisEntity, Scores):

    @property
    @override
    def fields(self) -> None:
        return None

    @override
    def values(self, *, reverse: bool = False) -> Awaitable[Iterator[str]]:
        return self._results.conv(self._redis_db.zrange(self._key_path, 0, -1, desc=reverse), iter)

    @override
    def scores(self, *, reverse: bool = False) -> Awaitable[Iterator[tuple[str, float]]]:
        return self._results.conv(
                self._redis_db.zrange(self._key_path, 0, -1, desc=reverse, withscores=True), iter)

    @override
    def index(self, key: str, *, reverse: bool = False) -> Awaitable[int | None]:
        zrank = self._redis_db.zrevrank if reverse else self._redis_db.zrank
        return self._results.asis(zrank(self._key_path, key))

    @override
    def score(self, key: str) -> Awaitable[float | None]:
        return self._results.asis(self._redis_db.zscore(self._key_path, key))

    @override
    def count(self) -> Awaitable[int]:
        return self._results.asis(self._redis_db.zcount(self._key_path, -math.inf, math.inf))

    @override
    def len(self) -> Awaitable[int]:
        return self._results.asis(self._redis_db.zcard(self._key_path))

    @override
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False,
               ) -> Awaitable[bool]:
        return self._results.conv(
                self._redis_db.zadd(self._key_path, {key: score}, xx=xx, nx=nx), bool)

    @override
    def remove(self, key: str) -> Awaitable[bool]:
        return self._results.conv(self._redis_db.zrem(self._key_path, key), bool)
