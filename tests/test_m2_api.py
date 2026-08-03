import struct

import numpy as np
import pytest

import accudist as ad


def bits(value):
    return "0x" + struct.pack(">d", float(value)).hex()


@pytest.mark.parametrize(
    ("call", "expected"),
    [
        (lambda: ad.pnorm(1.25, 0.5, 2, lower_tail=False, log=True), "0xbff09f7d809a7664"),
        (lambda: ad.qnorm(-1000, log=True), "0xc0464ed0d259b287"),
        (
            lambda: ad.pbinom(900, 1000, 1 / 6, lower_tail=False, log=True),
            "0xc09482c07c1c0914",
        ),
        (lambda: ad.gammafn(2.5), "0x3ff544fa6d47b390"),
        (lambda: ad.cospi(0.25), "0x3fe6a09e667f3bcc"),
    ],
)
def test_generated_m2_functions_match_r_bits(call, expected):
    assert bits(call()) == expected


def test_gamma_rate_and_scale_resolve_to_the_same_c_parameter():
    expected = "0xc01037635473696b"
    assert bits(ad.pgamma(3, 2, rate=2, lower_tail=False, log=True)) == expected
    assert bits(ad.pgamma(3, 2, scale=0.5, lower_tail=False, log=True)) == expected
    with pytest.warns(UserWarning, match="both 'rate' and 'scale'"):
        assert bits(
            ad.pgamma(3, 2, rate=2, scale=0.5, lower_tail=False, log=True)
        ) == expected
    with pytest.raises(TypeError, match="inconsistent 'rate' and 'scale'"):
        ad.pgamma(3, 2, rate=2, scale=9)


def test_negative_binomial_requires_exactly_one_parameterization():
    assert bits(ad.pnbinom(5, 10, prob=0.3, lower_tail=False, log=True)) == "0xbf6df9ea33c66cce"
    assert bits(ad.pnbinom(5, 10, mu=7, lower_tail=False, log=True)) == "0xbfdd4cce5325b62f"
    with pytest.raises(TypeError, match="exactly one of 'prob' or 'mu'"):
        ad.pnbinom(5, 10)
    with pytest.raises(TypeError, match="exactly one of 'prob' or 'mu'"):
        ad.pnbinom(5, 10, prob=0.3, mu=7)


def test_ncp_none_and_zero_select_distinct_r_algorithms():
    central = ad.pchisq(3, 5, lower_tail=False, log=True)
    noncentral_zero = ad.pchisq(3, 5, ncp=0.0, lower_tail=False, log=True)
    assert bits(central) == "0xbfd6d41803af4962"
    assert bits(noncentral_zero) == "0xbfd6d41803af4964"
    assert central != noncentral_zero


def test_m2_ufuncs_broadcast_and_preserve_out():
    out = np.empty(3)
    returned = ad.pnorm(np.array([-1.0, 0.0, 1.0]), out=out)
    assert returned is out
    np.testing.assert_allclose(out, [0.15865525393145705, 0.5, 0.8413447460685429])

