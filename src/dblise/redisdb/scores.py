
import math

from collections.abc import Iterator

from typing import override

from dblise.schemas import Scores

from .entity import RedisEntity


class RedisScores(RedisEntity, Scores):

    @override
    def __len__(self) -> int:
        return self._redis_db.zcard(self._key_path)

    @override
    def __iter__(self) -> Iterator[str]:
        yield from self.values()

    @override
    def values(self, *, reverse: bool = False) -> Iterator[str]:
        yield from self._redis_db.zrange(self._key_path, 0, -1, desc=reverse)

    @override
    def scores(self, *, reverse: bool = False) -> Iterator[tuple[str, float]]:
        yield from self._redis_db.zrange(self._key_path, 0, -1, desc=reverse, withscores=True)

    @override
    def index(self, key: str, *, reverse: bool = False) -> int | None:
        zrank = self._redis_db.zrevrank if reverse else self._redis_db.zrank
        return zrank(self._key_path, key)

    @override
    def score(self, key: str) -> float | None:
        return self._redis_db.zscore(self._key_path, key)

    @override
    def count(self) -> int:
        return self._redis_db.zcount(self._key_path, -math.inf, math.inf)

    @override
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False) -> None:
        self._redis_db.zadd(self._key_path, {key: score}, xx=xx, nx=nx)

    @override
    def remove(self, key: str) -> bool:
        return bool(self._redis_db.zrem(self._key_path, key))
