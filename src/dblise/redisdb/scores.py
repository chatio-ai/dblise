
import math

from collections.abc import Sequence
from typing import override

from dblise.schemas import Scores
from dblise.schemas import Result

from .entity import RedisEntity


class RedisScores(RedisEntity, Scores):

    @property
    @override
    def fields(self) -> None:
        return None

    @override
    def values(self, *, reverse: bool = False) -> Result[Sequence[str]]:
        return self._broker.same(lambda redis: redis.zrange(self._key_path, 0, -1, desc=reverse))

    @override
    def scores(self, *, reverse: bool = False) -> Result[Sequence[tuple[str, float]]]:
        return self._broker.same(
            lambda redis: redis.zrange(self._key_path, 0, -1, desc=reverse, withscores=True))

    @override
    def index(self, key: str, *, reverse: bool = False) -> Result[int | None]:
        return self._broker.same(
            lambda redis: (redis.zrevrank if reverse else redis.zrank)(self._key_path, key))

    @override
    def score(self, key: str) -> Result[float | None]:
        return self._broker.same(lambda redis: redis.zscore(self._key_path, key))

    @override
    def count(self) -> Result[int]:
        return self._broker.same(lambda redis: redis.zcount(self._key_path, -math.inf, math.inf))

    @override
    def len(self) -> Result[int]:
        return self._broker.same(lambda redis: redis.zcard(self._key_path))

    @override
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False,
               ) -> Result[bool]:
        return self._broker.cast(
                lambda redis: redis.zadd(self._key_path, {key: score}, xx=xx, nx=nx), bool)

    @override
    def remove(self, *keys: str) -> Result[int]:
        if not keys:
            return self._broker.pure(value=0)
        return self._broker.same(lambda redis: redis.zrem(self._key_path, *keys))
