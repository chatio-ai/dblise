
from typing import Optional
from typing import Union

import pytest

from dblise.helpers.typing import TypeId

# ruff: noqa: UP007
# ruff: noqa: UP045


CASES = [
    (bool, TypeId(raw_type=bool, optional=False)),
    (int, TypeId(raw_type=int, optional=False)),
    (None | bool, TypeId(raw_type=bool, optional=True)),
    (None | int, TypeId(raw_type=int, optional=True)),
    (bool | None, TypeId(raw_type=bool, optional=True)),
    (int | None, TypeId(raw_type=int, optional=True)),
    (Optional[bool], TypeId(raw_type=bool, optional=True)),
    (Optional[int], TypeId(raw_type=int, optional=True)),
    (Union[bool, None], TypeId(raw_type=bool, optional=True)),
    (Union[int, None], TypeId(raw_type=int, optional=True)),
    (Union[None, bool], TypeId(raw_type=bool, optional=True)),
    (Union[None, int], TypeId(raw_type=int, optional=True)),
]


@pytest.mark.parametrize(('value', 'result'), CASES)
def test_type_id(value: type, result: TypeId) -> None:
    assert TypeId.parse(value) == result
