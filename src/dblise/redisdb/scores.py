
import math

from collections.abc import Awaitable
from collections.abc import Sequence
from typing import override

from dblise.schemas import Scores

from .entity import RedisEntity
from .result import RedisResult


class RedisScores(RedisEntity, Scores):

    @property
    @override
    def fields(self) -> None:
        return None

    @override
    def values(self, *, reverse: bool = False) -> Awaitable[Sequence[str]]:
        return RedisResult.same(
            self._engine, self._engine.client.zrange(self._key_path, 0, -1, desc=reverse))

    @override
    def scores(self, *, reverse: bool = False) -> Awaitable[Sequence[tuple[str, float]]]:
        return RedisResult.same(
            self._engine,
            self._engine.client.zrange(self._key_path, 0, -1, desc=reverse, withscores=True))

    @override
    def index(self, key: str, *, reverse: bool = False) -> Awaitable[int | None]:
        zrank = self._engine.client.zrevrank if reverse else self._engine.client.zrank
        return RedisResult.same(self._engine, zrank(self._key_path, key))

    @override
    def score(self, key: str) -> Awaitable[float | None]:
        return RedisResult.same(
            self._engine, self._engine.client.zscore(self._key_path, key))

    @override
    def count(self) -> Awaitable[int]:
        return RedisResult.same(
            self._engine, self._engine.client.zcount(self._key_path, -math.inf, math.inf))

    @override
    def len(self) -> Awaitable[int]:
        return RedisResult.same(
            self._engine, self._engine.client.zcard(self._key_path))

    @override
    def insert(self, key: str, score: float, *, xx: bool = False, nx: bool = False,
               ) -> Awaitable[bool]:
        return RedisResult(
            self._engine,
            self._engine.client.zadd(self._key_path, {key: score}, xx=xx, nx=nx), bool)

    @override
    def remove(self, key: str) -> Awaitable[bool]:
        return RedisResult(
            self._engine, self._engine.client.zrem(self._key_path, key), bool)
