
from collections.abc import Iterator

from dblise.schemas import Entity
from dblise.schemas import Schema


def items_of(schema: Schema) -> Iterator[tuple[str, Entity]]:
    for name, entity in vars(schema).items():
        if not isinstance(entity, Entity):
            raise TypeError(entity)

        yield name, entity


def entities(*objs: object) -> Iterator[Entity]:
    for obj in objs:
        if isinstance(obj, Entity):
            yield obj
        elif isinstance(obj, Schema):
            for _, entity in items_of(obj):
                yield entity
        else:
            raise TypeError(obj)
