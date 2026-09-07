"""Layer 2: mathematical identities over wide parameter ranges (no oracle needed)."""

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

import accudist as ad

SETTINGS = dict(max_examples=200, deadline=None)

# moderate ranges: outside them quantiles legitimately round to 0, 1 or +-inf in double precision
positive = st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False)
unit = st.floats(min_value=1e-6, max_value=1 - 1e-6)
real = st.floats(min_value=-50, max_value=50, allow_nan=False, allow_infinity=False)

CONTINUOUS = {
    "norm": (lambda: (real,), lambda x, mean: (x, mean), None),
}


@settings(**SETTINGS)
@given(x=real, mean=real, sd=positive)
def test_norm_tails_and_log(x, mean, sd):
    lo = ad.pnorm(x, mean, sd)
    up = ad.pnorm(x, mean, sd, lower_tail=False)
    assert lo + up == pytest.approx(1.0, abs=1e-14)
    assert ad.pnorm(x, mean, sd, log=True) <= 0
    if lo > 1e-300:
        assert np.exp(ad.pnorm(x, mean, sd, log=True)) == pytest.approx(lo, rel=1e-12)
    # both tails carry full relative precision only away from 1; near 1 the
    # round-trip is limited by the spacing of doubles, not by the algorithm
    if 1e-6 < lo < 1 - 1e-6:
        assert ad.qnorm(lo, mean, sd) == pytest.approx(x, rel=1e-8, abs=1e-8 * sd)
        assert ad.qnorm(up, mean, sd, lower_tail=False) == pytest.approx(x, rel=1e-8, abs=1e-8 * sd)
    assert ad.dnorm(x, mean, sd) >= 0
    d = ad.dnorm(x, mean, sd)
    if d > 0:
        assert ad.dnorm(x, mean, sd, log=True) == pytest.approx(np.log(d), rel=1e-12)


@settings(**SETTINGS)
@given(q=positive, shape=positive, scale=positive)
def test_gamma_identities(q, shape, scale):
    lo = ad.pgamma(q, shape, scale=scale)
    up = ad.pgamma(q, shape, scale=scale, lower_tail=False)
    assert lo + up == pytest.approx(1.0, abs=1e-13)
    assert ad.pgamma(q, shape, scale=scale, log=True) <= 1e-15
    if 1e-10 < lo < 1 - 1e-10:
        assert ad.qgamma(lo, shape, scale=scale) == pytest.approx(q, rel=1e-7)
    assert ad.pgamma(q, shape, rate=1 / scale) == pytest.approx(lo, rel=1e-12)


@settings(**SETTINGS)
@given(p=unit, shape1=positive, shape2=positive)
def test_beta_quantile_roundtrip(p, shape1, shape2):
    q = ad.qbeta(p, shape1, shape2)
    assert 0 <= q <= 1
    if 1e-300 < q < 1 - 1e-15:
        assert ad.pbeta(q, shape1, shape2) == pytest.approx(p, rel=1e-7, abs=1e-12)
        assert ad.qbeta(1 - p, shape1, shape2, lower_tail=False) == pytest.approx(q, rel=1e-7, abs=1e-12)


@settings(**SETTINGS)
@given(p=unit, df=positive)
def test_t_and_chisq_quantile_roundtrip(p, df):
    assert ad.pt(ad.qt(p, df), df) == pytest.approx(p, rel=1e-7)
    assert ad.pchisq(ad.qchisq(p, df), df) == pytest.approx(p, rel=1e-7)
    assert ad.pchisq(ad.qchisq(p, df, ncp=1.5), df, ncp=1.5) == pytest.approx(p, rel=1e-6)


@settings(**SETTINGS)
@given(size=st.integers(0, 200), prob=unit)
def test_binomial_mass_sums_and_cdf_matches_partial_sums(size, prob):
    k = np.arange(size + 1)
    d = ad.dbinom(k, size, prob)
    assert np.all(d >= 0)
    assert d.sum() == pytest.approx(1.0, abs=1e-12)
    np.testing.assert_allclose(ad.pbinom(k, size, prob), np.cumsum(d), rtol=1e-10, atol=1e-14)
    assert np.all(np.diff(ad.pbinom(k, size, prob)) >= -1e-15)
    assert np.all(ad.dbinom(k, size, prob, log=True) <= 1e-15)


@settings(**SETTINGS)
@given(lam=st.floats(min_value=1e-3, max_value=500), q=st.integers(0, 2000))
def test_poisson_tails(lam, q):
    lo = ad.ppois(q, lam)
    up = ad.ppois(q, lam, lower_tail=False)
    assert lo + up == pytest.approx(1.0, abs=1e-13)
    assert ad.ppois(q, lam, lower_tail=False, log=True) <= 1e-15
    assert np.isfinite(ad.ppois(q, lam, lower_tail=False, log=True)) or up == 0.0 and lo == 1.0


@settings(**SETTINGS)
@given(x=st.floats(min_value=0.05, max_value=170, allow_nan=False))
def test_gamma_function_recurrence(x):
    assert ad.gammafn(x + 1) == pytest.approx(x * ad.gammafn(x), rel=1e-12)
    assert ad.lgammafn(x) == pytest.approx(np.log(abs(ad.gammafn(x))), rel=1e-12, abs=1e-12)
    assert ad.digamma(x + 1) == pytest.approx(ad.digamma(x) + 1 / x, rel=1e-10, abs=1e-12)
