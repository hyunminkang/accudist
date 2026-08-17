"""Numerical comparison policy for values recorded from R."""

import math
import struct

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

_EXPONENT_MASK = 0x7FF0000000000000
_FRACTION_MASK = 0x000FFFFFFFFFFFFF
_MAGNITUDE_MASK = 0x7FFFFFFFFFFFFFFF

# Covers the measured Windows MSVC/libm differences from the official R build while
# remaining several orders of magnitude tighter than the public API's invariants.
REFERENCE_RELATIVE_TOLERANCE = 1e-10


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
    """Compare an implementation result with an R reference value.

    Exact values and NaNs are handled first. Finite values then use the package-wide
    relative tolerance, with no absolute tolerance so near-zero tail results cannot
    disappear. Historical per-function ULP allowances remain as a narrower fallback
    for subnormal and other edge cases.
    """

    if same_oracle_value(actual, expected):
        return True
    actual_value = struct.unpack(">d", actual)[0]
    expected_value = struct.unpack(">d", expected)[0]
    if math.isfinite(actual_value) and math.isfinite(expected_value) and math.isclose(
        actual_value,
        expected_value,
        rel_tol=REFERENCE_RELATIVE_TOLERANCE,
        abs_tol=0.0,
    ):
        return True
    return (
        max_ulp is not None
        and can_apply_ulp_waiver(actual, expected)
        and abs(_ordered_bits(actual) - _ordered_bits(expected)) <= max_ulp
    )


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
