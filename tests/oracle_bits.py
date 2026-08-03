"""Comparison policy for raw IEEE-754 oracle values."""

_EXPONENT_MASK = 0x7FF0000000000000
_FRACTION_MASK = 0x000FFFFFFFFFFFFF
_MAGNITUDE_MASK = 0x7FFFFFFFFFFFFFFF


def _bits(raw: bytes) -> int:
    if len(raw) != 8:
        raise ValueError("an oracle value must contain exactly eight bytes")
    return int.from_bytes(raw, "big")


def _is_nan(bits: int) -> bool:
    return bits & _EXPONENT_MASK == _EXPONENT_MASK and bool(bits & _FRACTION_MASK)


def same_oracle_value(actual: bytes, expected: bytes) -> bool:
    """Return whether two binary64 results satisfy the oracle contract.

    Non-NaN values match only when all 64 bits match. Any two NaN encodings match,
    because IEEE-754 does not assign semantic meaning to a NaN's sign or payload.
    """

    actual_bits = _bits(actual)
    expected_bits = _bits(expected)
    return actual_bits == expected_bits or (
        _is_nan(actual_bits) and _is_nan(expected_bits)
    )


def can_apply_ulp_waiver(actual: bytes, expected: bytes) -> bool:
    """Return whether a bounded ULP waiver may compare these values."""

    actual_bits = _bits(actual)
    expected_bits = _bits(expected)
    return all(
        bits & _EXPONENT_MASK != _EXPONENT_MASK
        and bits & _MAGNITUDE_MASK != 0
        for bits in (actual_bits, expected_bits)
    )
