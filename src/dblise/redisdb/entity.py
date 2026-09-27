
from typing import override

from dblise.schemas import Entity
from dblise.schemas import Result

from .result import RedisBroker


class RedisEntity(Entity):

    def __init__(self, broker: RedisBroker, key_path: str) -> None:
        self._broker = broker
        self._key_path = key_path

    @property
    @override
    def handle(self) -> str:
        return self._key_path

    @override
    def exists(self) -> Result[bool]:
        return self._broker.cast(lambda redis: redis.exists(self._key_path), bool)

    @override
    def delete(self) -> Result[bool]:
        return self._broker.cast(lambda redis: redis.unlink(self._key_path), bool)
