
from decimal import Decimal

from typing import TYPE_CHECKING

import redis


type FieldDict = dict[str, str | bool | int | float | Decimal | None]
type RedisDict = dict[str, str]


if TYPE_CHECKING:
    type Redis = redis.Redis[str]
    type Pipeline = redis.client.Pipeline[str]
else:
    Redis = redis.Redis
    Pipeline = redis.client.Pipeline
