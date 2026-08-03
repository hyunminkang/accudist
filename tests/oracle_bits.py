"""Comparison policy for raw IEEE-754 oracle values."""

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

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


def _ordered_bits(raw: bytes) -> int:
    bits = _bits(raw)
    return (~bits & ((1 << 64) - 1)) if bits >> 63 else bits | (1 << 63)


def matches_oracle_value(
    actual: bytes, expected: bytes, *, max_ulp: int | None = None
) -> bool:
    """Apply exact oracle semantics plus an optional reviewed ULP budget."""

    if same_oracle_value(actual, expected):
        return True
    if max_ulp is None or not can_apply_ulp_waiver(actual, expected):
        return False
    return abs(_ordered_bits(actual) - _ordered_bits(expected)) <= max_ulp


def load_ulp_waivers(path, platform: str) -> dict[str, int]:
    """Load the reviewed per-function budgets active on one platform."""

    document = tomllib.loads(path.read_text())
    result = {}
    for waiver in document.get("waiver", []):
        assert 0 < waiver["max_ulp"] <= 4
        assert waiver["reason"]
        if platform in waiver["platforms"]:
            result[waiver["func"]] = waiver["max_ulp"]
    return result
