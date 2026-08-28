
from decimal import Decimal


def str_to_decimal(value: str, n_digits: int | None = None) -> Decimal:
    num = Decimal(value)
    return num if n_digits is None else round(num, n_digits)


def decimal_to_str(num: Decimal, n_digits: int | None = None) -> str:
    num = num if n_digits is None else round(num, n_digits)
    return format(num.normalize(), 'zf')
