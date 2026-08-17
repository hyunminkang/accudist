from pathlib import Path

import pytest

from oracle_bits import (
    can_apply_ulp_waiver,
    load_ulp_waivers,
    matches_oracle_value,
    same_oracle_value,
)


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("7ff8000000000000", "fff8000000000000"),
        ("7ff8000000000001", "7ff8000000000042"),
        ("fff8000000000001", "7ff8000000000042"),
    ],
)
def test_nan_sign_and_payload_are_not_part_of_the_oracle_value(actual, expected):
    assert same_oracle_value(bytes.fromhex(actual), bytes.fromhex(expected))


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("0000000000000000", "8000000000000000"),
        ("7ff0000000000000", "fff0000000000000"),
        ("3ff0000000000000", "3ff0000000000001"),
        ("7ff8000000000000", "7ff0000000000000"),
    ],
)
def test_every_non_nan_oracle_value_remains_bit_exact(actual, expected):
    assert not same_oracle_value(bytes.fromhex(actual), bytes.fromhex(expected))


def test_identical_bits_match():
    value = bytes.fromhex("bff0000000000000")
    assert same_oracle_value(value, value)


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("43abc16bd272fb4b", "43abc16bd273e705"),
        ("43abc16d8f457c01", "43abc16d8f44deda"),
        ("426d1a94a20034a4", "426d1a94a20034a3"),
    ],
)
def test_windows_libm_rounding_matches_the_r_reference(actual, expected):
    assert matches_oracle_value(bytes.fromhex(actual), bytes.fromhex(expected))


@pytest.mark.parametrize(
    ("actual", "expected", "allowed"),
    [
        ("3ff0000000000000", "3ff0000000000001", True),
        ("0000000000000000", "8000000000000000", False),
        ("0000000000000000", "0000000000000001", False),
        ("7fefffffffffffff", "7ff0000000000000", False),
        ("7ff0000000000000", "7ff8000000000000", False),
        ("7ff8000000000000", "fff8000000000000", False),
    ],
)
def test_ulp_waivers_apply_only_to_finite_nonzero_results(actual, expected, allowed):
    assert (
        can_apply_ulp_waiver(bytes.fromhex(actual), bytes.fromhex(expected))
        is allowed
    )


@pytest.mark.parametrize(
    ("actual", "expected", "max_ulp", "matches"),
    [
        ("3ff0000000000000", "3ff0000000000000", None, True),
        ("3ff0000000000001", "3ff0000000000000", None, True),
        ("3ff0000000000002", "3ff0000000000000", 2, True),
        ("3ff0000000036f9c", "3ff0000000000000", None, True),
        ("3ff000000044b830", "3ff0000000000000", None, False),
        ("bff0000000000002", "bff0000000000000", 2, True),
        ("8000000000000000", "0000000000000000", None, True),
        ("0000000000000003", "0000000000000001", 2, True),
    ],
)
def test_reference_matching_applies_the_global_tolerance_and_ulp_fallback(
    actual, expected, max_ulp, matches
):
    assert (
        matches_oracle_value(
            bytes.fromhex(actual), bytes.fromhex(expected), max_ulp=max_ulp
        )
        is matches
    )


def test_linux_waivers_cover_only_the_reviewed_observed_distances():
    waivers = load_ulp_waivers(
        Path(__file__).parent / "ulp_waivers.toml", "linux-x86_64"
    )
    observed = [
        ("pbinom", "c09482c07c1c0915", "c09482c07c1c0914"),
        ("cospi", "3fe6a09e667f3bcd", "3fe6a09e667f3bcc"),
        ("bessel_y", "3fd24f067ebdf822", "3fd24f067ebdf820"),
        ("tetragamma", "fe47e43c8800759c", "fe47e43c8800759b"),
    ]
    for function, actual, expected in observed:
        assert matches_oracle_value(
            bytes.fromhex(actual),
            bytes.fromhex(expected),
            max_ulp=waivers[function],
        )
