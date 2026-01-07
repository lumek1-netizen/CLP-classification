from typing import Optional, Union


def get_float_or_none(value: Optional[Union[str, float]]) -> Optional[float]:
    """Převede string na float nebo vrátí None."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_int_or_default(
    value: Optional[Union[str, int, float]], default: int = 1
) -> int:
    """Převede string na celé číslo nebo vrátí default."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default
