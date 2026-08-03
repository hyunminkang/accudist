import numpy as np
import pytest
from hypothesis import given, seed, settings, strategies as st

import accudist as ad


CDF_CASES = [
    (ad.pnorm, (0.0, 1.0)),
    (ad.pgamma, (2.0,)),
    (ad.pbeta, (2.0, 3.0)),
    (ad.pchisq, (5.0,)),
    (ad.pt, (7.0,)),
    (ad.pf, (5.0, 9.0)),
    (ad.pexp, (2.0,)),
    (ad.pweibull, (1.5, 2.0)),
    (ad.plnorm, (0.0, 1.0)),
    (ad.pcauchy, (0.0, 1.0)),
    (ad.plogis, (0.0, 1.0)),
    (ad.punif, (-2.0, 3.0)),
    (ad.pbinom, (20.0, 0.3)),
    (ad.ppois, (4.0,)),
    (ad.pnbinom, (5.0, 0.4)),
    (ad.pgeom, (0.3,)),
    (ad.phyper, (7.0, 13.0, 5.0)),
    (ad.pchisq, (5.0, 1.5)),
    (ad.pwilcox, (5.0, 6.0)),
    (ad.psignrank, (8.0,)),
    (ad.ptukey, (5.0, 20.0, 1.0)),
]


@pytest.mark.parametrize(("cdf", "parameters"), CDF_CASES)
@settings(max_examples=40, deadline=None, database=None)
@seed(452)
@given(st.integers(min_value=-2_000, max_value=2_000).map(lambda value: value / 100.0))
def test_cdf_tail_log_and_monotonic_invariants(cdf, parameters, x):
    lower = cdf(x, *parameters)
    upper = cdf(x, *parameters, lower_tail=False)
    logged = cdf(x, *parameters, log=True)
    assert lower + upper == pytest.approx(1.0, rel=1e-14, abs=1e-15)
    assert logged <= 0
    if lower > 0:
        assert np.exp(logged) == pytest.approx(lower, rel=1e-14, abs=0)
    assert cdf(x - 1e-7, *parameters) <= cdf(x + 1e-7, *parameters)


@settings(max_examples=80, deadline=None, database=None)
@seed(452)
@given(
    st.floats(min_value=-8, max_value=8, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.05, max_value=5, allow_nan=False, allow_infinity=False),
)
def test_normal_density_and_quantile_invariants(x, sd):
    density = ad.dnorm(x, sd=sd)
    assert density >= 0
    if density > 0:
        assert ad.dnorm(x, sd=sd, log=True) == pytest.approx(np.log(density), rel=1e-14)
    p = ad.pnorm(x, sd=sd)
    if 1e-12 < p < 1 - 1e-12:
        assert ad.qnorm(p, sd=sd) == pytest.approx(x, rel=1e-9, abs=1e-10)
        assert ad.qnorm(p, sd=sd) == pytest.approx(ad.qnorm(1 - p, sd=sd, lower_tail=False), rel=1e-9)


def test_nan_propagates_through_every_function_kind():
    assert np.isnan(ad.dnorm(np.nan))
    assert np.isnan(ad.pnorm(np.nan))
    assert np.isnan(ad.qnorm(np.nan))
    assert np.isnan(ad.gammafn(np.nan))
