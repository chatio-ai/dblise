
from typing import Optional
from typing import Union

import pytest

from dblise.helpers.typing import FieldTypeId

# ruff: noqa: UP007
# ruff: noqa: UP045


CASES = [
    (bool, FieldTypeId(raw_type=bool, optional=False)),
    (int, FieldTypeId(raw_type=int, optional=False)),
    (None | bool, FieldTypeId(raw_type=bool, optional=True)),
    (None | int, FieldTypeId(raw_type=int, optional=True)),
    (bool | None, FieldTypeId(raw_type=bool, optional=True)),
    (int | None, FieldTypeId(raw_type=int, optional=True)),
    (Optional[bool], FieldTypeId(raw_type=bool, optional=True)),
    (Optional[int], FieldTypeId(raw_type=int, optional=True)),
    (Union[bool, None], FieldTypeId(raw_type=bool, optional=True)),
    (Union[int, None], FieldTypeId(raw_type=int, optional=True)),
    (Union[None, bool], FieldTypeId(raw_type=bool, optional=True)),
    (Union[None, int], FieldTypeId(raw_type=int, optional=True)),
]


@pytest.mark.parametrize(('value', 'result'), CASES)
def test_type_id(value: type, result: FieldTypeId) -> None:
    assert FieldTypeId.parse(value) == result
