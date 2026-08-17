import struct
import sys
from pathlib import Path

import numpy as np
import pytest

import accudist as ad
from accudist._platform import platform_id
from oracle_bits import load_ulp_waivers, matches_oracle_value

if sys.platform != "win32":
    import resource


ULP_WAIVERS = load_ulp_waivers(
    Path(__file__).parent / "ulp_waivers.toml", platform_id()
)


def matches_r_reference(value, expected, function):
    return matches_oracle_value(
        struct.pack(">d", float(value)),
        bytes.fromhex(expected.removeprefix("0x")),
        max_ulp=ULP_WAIVERS.get(function),
    )


def test_tukey_public_order_is_reordered_for_rmath():
    assert matches_r_reference(
        ad.ptukey(3.5, nmeans=5, df=20, nranges=1),
        "0x3feba1c5d2045191",
        "ptukey",
    )
    assert matches_r_reference(
        ad.qtukey(0.95, nmeans=5, df=20, nranges=1),
        "0x4010ed6bd69a2e08",
        "qtukey",
    )


def test_rank_distributions_match_r():
    assert matches_r_reference(
        ad.pwilcox(12, 5, 6, lower_tail=False, log=True),
        "0xbfd9be081d2658db",
        "pwilcox",
    )
    assert matches_r_reference(
        ad.psignrank(12, 8, lower_tail=False, log=True),
        "0xbfd0c42d676162e4",
        "psignrank",
    )


@pytest.mark.parametrize(
    ("function", "call", "expected"),
    [
        (
            "bessel_i",
            lambda: ad.bessel_i(2.5, 0.75, expon_scaled=True),
            "0x3fcd86f98b0cf10f",
        ),
        (
            "bessel_k",
            lambda: ad.bessel_k(2.5, 0.75, expon_scaled=True),
            "0x3feabff5c4f42404",
        ),
        ("bessel_j", lambda: ad.bessel_j(2.5, 0.75), "0x3fdb0700da825d64"),
        ("bessel_y", lambda: ad.bessel_y(2.5, 0.75), "0x3fd24f067ebdf820"),
    ],
)
def test_bessel_wrappers_match_r(function, call, expected):
    assert matches_r_reference(call(), expected, function)


def test_pnorm_both_returns_direct_lower_and_upper_tails():
    lower, upper = ad.pnorm_both(8.0, log=True)
    assert matches_r_reference(lower, "0xbcc669d2c90d55d1", "pnorm_both")
    assert matches_r_reference(upper, "0xc04181b84f11312b", "pnorm_both")


def test_lgammafn_sign_returns_value_and_sign():
    value, sign = ad.lgammafn_sign(np.array([-2.5, 2.5]))
    assert matches_r_reference(value[0], "0xbfaccbf9f5ed0f13", "lgammafn_sign")
    assert sign.tolist() == [-1, 1]


def test_lgammafn_sign_does_not_reconstruct_sign_from_underflowed_gamma():
    value, sign = ad.lgammafn_sign(-200.5)
    assert np.isfinite(value)
    assert sign == -1


@pytest.mark.skipif(sys.platform == "win32", reason="resource usage is unavailable on Windows")
def test_wilcox_cache_has_no_sustained_growth_across_varying_shapes():
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for index in range(10_000):
        m = 2 + index % 13
        n = 2 + (index * 7) % 13
        ad.pwilcox((m * n) // 2, m, n)
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    units = 1 if sys.platform == "darwin" else 1024
    assert (after - before) * units < 64 * 1024 * 1024
