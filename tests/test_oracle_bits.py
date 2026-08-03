import pytest

from oracle_bits import can_apply_ulp_waiver, same_oracle_value


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
