
import math

from collections.abc import Iterator

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
    def values(self, *, reverse: bool = False) -> Result[Iterator[str]]:
        return Result(self._redis_db.zrange(self._key_path, 0, -1, desc=reverse), iter)

    @override
    def scores(self, *, reverse: bool = False) -> Result[Iterator[tuple[str, float]]]:
        return Result(
                self._redis_db.zrange(self._key_path, 0, -1, desc=reverse, withscores=True), iter)

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
