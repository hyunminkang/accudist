"""Signature, dispatch and broadcasting behaviour of the public API."""

import numpy as np
import pytest

import accudist as ad


def test_motivating_values():
    assert ad.ppois(200, 0.1, lower_tail=False, log=True) == pytest.approx(-1331.4544006213939, rel=1e-12)
    assert ad.pbinom(900, 1000, 1 / 6, lower_tail=False, log=True) == pytest.approx(-1312.6879734, rel=1e-9)
    assert ad.qnorm(-1000, log=True) == pytest.approx(-44.6157477319694, rel=1e-12)
    assert ad.pgamma(1e5, 2, lower_tail=False, log=True) == pytest.approx(-99988.48706, rel=1e-9)


def test_scalar_returns_numpy_float64():
    r = ad.pnorm(0.0)
    assert isinstance(r, np.float64)
    assert r == 0.5


def test_broadcasting_and_out():
    q = np.arange(100, 105)
    r = ad.ppois(q, 0.1, lower_tail=False, log=True)
    assert r.shape == (5,)
    assert np.all(np.diff(r) < 0)
    out = np.empty(5)
    r2 = ad.ppois(q, 0.1, lower_tail=False, log=True, out=out)
    assert r2 is out
    np.testing.assert_array_equal(out, r)
    grid = ad.dnorm(np.zeros((3, 1)), mean=np.array([0.0, 1.0]), sd=1.0)
    assert grid.shape == (3, 2)


def test_integer_and_bool_inputs_cast_to_double():
    assert ad.dbinom(3, 10, 0.5) == pytest.approx(0.1171875)
    assert ad.pnorm(np.arange(3, dtype=np.int64)).shape == (3,)
    assert ad.pnorm(1.0, 0, 1, True, False) == ad.pnorm(1.0)
    assert ad.pnorm(1.0, lower_tail=0) == ad.pnorm(1.0, lower_tail=False)


def test_quantiles_of_discrete_distributions_are_doubles():
    r = ad.qpois(0.5, 4.0)
    assert isinstance(r, np.float64) and r == 4.0


def test_log_is_the_only_spelling():
    with pytest.raises(TypeError):
        ad.ppois(1, 2, log_p=True)
    with pytest.raises(TypeError):
        ad.dnorm(1, give_log=True)


def test_lambda_underscore():
    assert ad.dpois(2, lambda_=3.0) == ad.dpois(2, 3.0)


def test_ncp_none_versus_zero_take_different_paths():
    central = ad.pchisq(3.0, df=5)
    noncentral0 = ad.pchisq(3.0, df=5, ncp=0.0)
    assert central == pytest.approx(noncentral0, rel=1e-10)
    assert ad.pchisq(3.0, df=5, ncp=1.5) < central
    for fn, args in [(ad.dt, (0.5, 4)), (ad.pt, (0.5, 4)), (ad.qt, (0.3, 4)),
                     (ad.df, (0.5, 3, 7)), (ad.pf, (0.5, 3, 7)), (ad.qf, (0.3, 3, 7)),
                     (ad.dbeta, (0.5, 2, 3)), (ad.pbeta, (0.5, 2, 3)), (ad.qbeta, (0.3, 2, 3)),
                     (ad.dchisq, (0.5, 4)), (ad.qchisq, (0.3, 4))]:
        assert fn(*args) == pytest.approx(fn(*args, ncp=0.0), rel=1e-8)
        assert fn(*args, ncp=2.0) != fn(*args)


def test_prob_xor_mu():
    assert ad.pnbinom(3, 5, prob=0.3) == pytest.approx(ad.pnbinom(3, 5, mu=5 * 0.7 / 0.3), rel=1e-12)
    with pytest.raises(TypeError, match="both"):
        ad.pnbinom(3, 5, 0.3, 7.0)
    with pytest.raises(TypeError, match="requires one of"):
        ad.pnbinom(3, 5)
    assert ad.dnbinom(2, 3, mu=4.0) == pytest.approx(ad.dnbinom(2, 3, prob=3 / 7), rel=1e-12)


def test_rate_xor_scale():
    assert ad.pgamma(2.0, 3, rate=2.0) == ad.pgamma(2.0, 3, scale=0.5)
    assert ad.pgamma(2.0, 3) == ad.pgamma(2.0, 3, rate=1.0)
    with pytest.warns(ad.AccudistWarning, match="not both"):
        ad.pgamma(2.0, 3, rate=2.0, scale=0.5)
    with pytest.raises(TypeError, match="not both"):
        ad.pgamma(2.0, 3, rate=2.0, scale=9.0)
    assert ad.dgamma(1.0, 2.0, rate=np.array([1.0, 2.0])).shape == (2,)


def test_exp_rate_transform():
    assert ad.dexp(1.0, rate=2.0) == pytest.approx(2.0 * np.exp(-2.0))
    assert ad.pexp(1.0, 2.0) == pytest.approx(1 - np.exp(-2.0))
    assert ad.qexp(0.5, 2.0) == pytest.approx(np.log(2) / 2)
    assert ad.dexp(1.0, rate=0.0) == 0.0  # R: dexp(1, 0) is 0 (scale = Inf)


def test_ptukey_argument_order():
    # R: ptukey(3.5, nmeans = 5, df = 20) == 0.8634976...; the C symbol takes (q, nranges, nmeans, df)
    assert ad.ptukey(3.5, nmeans=5, df=20) == pytest.approx(0.8634976484195694, rel=1e-10)
    assert ad.ptukey(3.5, 5, 20) == ad.ptukey(3.5, nmeans=5, df=20, nranges=1)
    assert ad.ptukey(3.5, nmeans=20, df=5) != ad.ptukey(3.5, nmeans=5, df=20)
    assert ad.qtukey(0.95, nmeans=5, df=20) == pytest.approx(4.231857, rel=1e-6)


def test_hyper_and_signrank_keep_r_names():
    assert ad.dhyper(1, m=10, n=7, k=8) == pytest.approx(10 / 24310, rel=1e-12)
    assert ad.rhyper(nn=3, m=10, n=7, k=8).shape == (3,)
    assert ad.rsignrank(nn=4, n=10).shape == (4,)
    assert ad.rwilcox(nn=2, m=4, n=6).shape == (2,)


def test_bessel_expon_scaled():
    assert ad.bessel_i(1.0, 0.5, expon_scaled=True) == pytest.approx(ad.bessel_i(1.0, 0.5) * np.exp(-1.0), rel=1e-12)
    assert ad.bessel_k(2.0, 1.0, expon_scaled=True) == pytest.approx(ad.bessel_k(2.0, 1.0) * np.exp(2.0), rel=1e-12)


def test_special_function_names_are_rmath_names():
    assert ad.gammafn(5.0) == 24.0
    assert ad.lgammafn(5.0) == pytest.approx(np.log(24.0))
    assert ad.psigamma(2.0, deriv=1) == pytest.approx(ad.trigamma(2.0))
    assert ad.choose(5, 2) == 10.0
    assert not hasattr(ad, "gamma")


def test_lower_tail_is_not_one_minus_cdf():
    assert np.isfinite(ad.ppois(200, 0.1, lower_tail=False, log=True))
    assert ad.ppois(200, 0.1, lower_tail=False) == 0.0  # underflows in linear space, as in R


def test_rmath_escape_hatch():
    from accudist import rmath

    assert rmath.pnchisq(3.0, 5.0, 1.5, 1, 0) == ad.pchisq(3.0, 5, ncp=1.5)
    assert rmath.dbinom_raw(3.0, 10.0, 0.5, 0.5, 0) == pytest.approx(ad.dbinom(3, 10, 0.5))
    assert rmath.dpois_raw(2.0, 3.0, 1) == pytest.approx(ad.dpois(2, 3.0, log=True))


def test_nan_in_nan_out():
    for fn, args in [(ad.pnorm, (np.nan,)), (ad.dpois, (np.nan, 2.0)), (ad.qbeta, (0.5, np.nan, 2.0)), (ad.gammafn, (np.nan,))]:
        assert np.isnan(fn(*args))


def test_version_metadata():
    assert ad.__r_version__ == "4.5.2"
    assert ad.__version__.count(".") >= 2
