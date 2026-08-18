
from decimal import Decimal

from typing import TYPE_CHECKING

from redis import client


type FieldDict = dict[str, str | bool | int | float | Decimal | None]
type RedisDict = dict[str, str]


if TYPE_CHECKING:
    type Redis = client.Redis[str]
    type Pipeline = client.Pipeline[str]
else:
    Redis = client.Redis
    Pipeline = client.Pipeline
