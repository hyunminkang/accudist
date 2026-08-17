import struct

import numpy as np
import pytest

import accudist as ad
from oracle_bits import matches_oracle_value


def test_poisson_upper_log_tail_matches_r_reference():
    actual = struct.pack(
        ">d", float(ad.ppois(200, 0.1, lower_tail=False, log=True))
    )
    assert matches_oracle_value(actual, bytes.fromhex("c094cdd14e6580ad"))


def test_ppois_broadcasts_and_honours_out():
    q = np.array([[0.0], [1.0], [2.0]])
    rate = np.array([0.1, 1.0])
    out = np.empty((3, 2))

    returned = ad.ppois(q, rate, out=out)

    assert returned is out
    np.testing.assert_allclose(
        out,
        [[0.9048374180359595, 0.36787944117144233],
         [0.9953211598395555, 0.7357588823428847],
         [0.9998453469297354, 0.9196986029286058]],
        rtol=1e-15,
        atol=0.0,
    )


def test_ppois_scalar_is_numpy_float64():
    assert isinstance(ad.ppois(2, 0.1), np.float64)


def test_domain_error_warns_and_returns_nan():
    with pytest.warns(ad.AccudistDomainWarning, match="argument out of domain in 'ppois'"):
        result = ad.ppois(2, -1)
    assert np.isnan(result)


def test_domain_error_can_raise():
    with ad.errstate(domain="raise"), pytest.raises(ad.AccudistDomainError):
        ad.ppois(2, -1)


def test_nested_errstate_restores_policy():
    with ad.errstate(domain="raise"):
        with ad.errstate(domain="ignore"):
            assert np.isnan(ad.ppois(2, -1))
        with pytest.raises(ad.AccudistDomainError):
            ad.ppois(2, -1)


def test_nmath_writes_nothing(capsys):
    with ad.errstate(all="ignore"):
        ad.ppois(2, -1)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
