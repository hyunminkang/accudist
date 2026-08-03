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
    (lambda x, *args, **kwargs: ad.pbeta(x, *args, ncp=1.5, **kwargs), (2.0, 3.0)),
    (lambda x, *args, **kwargs: ad.pf(x, *args, ncp=1.5, **kwargs), (5.0, 9.0)),
    (lambda x, *args, **kwargs: ad.pt(x, *args, ncp=1.5, **kwargs), (7.0,)),
]


@pytest.mark.parametrize(("cdf", "parameters"), CDF_CASES)
@settings(max_examples=40, deadline=None, database=None)
@seed(452)
@given(st.integers(min_value=-2_000, max_value=2_000).map(lambda value: value / 100.0))
def test_cdf_tail_log_and_monotonic_invariants(cdf, parameters, x):
    lower = cdf(x, *parameters)
    upper = cdf(x, *parameters, lower_tail=False)
    logged = cdf(x, *parameters, log=True)
    logged_upper = cdf(x, *parameters, lower_tail=False, log=True)
    assert lower + upper == pytest.approx(1.0, rel=1e-14, abs=1e-15)
    assert logged <= 0
    assert logged_upper <= 0
    if lower > 0:
        assert np.exp(logged) == pytest.approx(lower, rel=1e-14, abs=0)
    if upper > 0:
        assert np.exp(logged_upper) == pytest.approx(upper, rel=1e-14, abs=0)
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


DENSITY_CASES = [
    (ad.dnorm, 0.3, (0.0, 1.0), {}),
    (ad.dunif, 0.3, (-2.0, 3.0), {}),
    (ad.dgamma, 1.3, (2.0,), {}),
    (ad.dbeta, 0.3, (2.0, 3.0), {}),
    (ad.dlnorm, 1.3, (0.0, 1.0), {}),
    (ad.dchisq, 3.0, (5.0,), {}),
    (ad.df, 1.3, (5.0, 9.0), {}),
    (ad.dt, 0.3, (7.0,), {}),
    (ad.dbinom, 3.0, (20.0, 0.3), {}),
    (ad.dcauchy, 0.3, (0.0, 1.0), {}),
    (ad.dexp, 1.3, (2.0,), {}),
    (ad.dgeom, 3.0, (0.3,), {}),
    (ad.dhyper, 2.0, (7.0, 13.0, 5.0), {}),
    (ad.dnbinom, 3.0, (5.0, 0.4), {}),
    (ad.dpois, 3.0, (4.0,), {}),
    (ad.dweibull, 1.3, (1.5, 2.0), {}),
    (ad.dlogis, 0.3, (0.0, 1.0), {}),
    (ad.dwilcox, 10.0, (5.0, 6.0), {}),
    (ad.dsignrank, 10.0, (8.0,), {}),
    (ad.dbeta, 0.3, (2.0, 3.0), {"ncp": 1.5}),
    (ad.dchisq, 3.0, (5.0,), {"ncp": 1.5}),
    (ad.df, 1.3, (5.0, 9.0), {"ncp": 1.5}),
    (ad.dt, 0.3, (7.0,), {"ncp": 1.5}),
]


@pytest.mark.parametrize(("density", "x", "parameters", "kwargs"), DENSITY_CASES)
def test_every_density_is_nonnegative_and_matches_its_log_form(density, x, parameters, kwargs):
    linear = density(x, *parameters, **kwargs)
    logged = density(x, *parameters, log=True, **kwargs)
    assert linear >= 0
    if linear == 0:
        assert logged == -np.inf
    else:
        assert logged == pytest.approx(np.log(linear), rel=2e-14, abs=1e-14)


CONTINUOUS_ROUNDTRIPS = [
    (ad.pnorm, ad.qnorm, (0.0, 1.0), {}, [-3.0, 0.0, 2.0]),
    (ad.punif, ad.qunif, (-2.0, 3.0), {}, [-1.5, 0.0, 2.5]),
    (ad.pgamma, ad.qgamma, (2.0,), {}, [0.1, 1.0, 5.0]),
    (ad.pbeta, ad.qbeta, (2.0, 3.0), {}, [0.1, 0.5, 0.9]),
    (ad.plnorm, ad.qlnorm, (0.0, 1.0), {}, [0.1, 1.0, 5.0]),
    (ad.pchisq, ad.qchisq, (5.0,), {}, [0.1, 3.0, 10.0]),
    (ad.pf, ad.qf, (5.0, 9.0), {}, [0.1, 1.0, 5.0]),
    (ad.pt, ad.qt, (7.0,), {}, [-3.0, 0.0, 2.0]),
    (ad.pcauchy, ad.qcauchy, (0.0, 1.0), {}, [-3.0, 0.0, 2.0]),
    (ad.pexp, ad.qexp, (2.0,), {}, [0.1, 1.0, 5.0]),
    (ad.pweibull, ad.qweibull, (1.5, 2.0), {}, [0.1, 1.0, 5.0]),
    (ad.plogis, ad.qlogis, (0.0, 1.0), {}, [-3.0, 0.0, 2.0]),
    (ad.pbeta, ad.qbeta, (2.0, 3.0), {"ncp": 1.5}, [0.1, 0.5, 0.9]),
    (ad.pchisq, ad.qchisq, (5.0,), {"ncp": 1.5}, [0.1, 3.0, 10.0]),
    (ad.pf, ad.qf, (5.0, 9.0), {"ncp": 1.5}, [0.1, 1.0, 5.0]),
    (ad.pt, ad.qt, (7.0,), {"ncp": 1.5}, [-2.0, 0.0, 3.0]),
]


@pytest.mark.parametrize(("cdf", "quantile", "parameters", "kwargs", "values"), CONTINUOUS_ROUNDTRIPS)
def test_every_continuous_quantile_inverts_its_cdf(cdf, quantile, parameters, kwargs, values):
    for value in values:
        probability = cdf(value, *parameters, **kwargs)
        if 1e-12 < probability < 1 - 1e-12:
            assert quantile(probability, *parameters, **kwargs) == pytest.approx(
                value, rel=1e-8, abs=1e-9
            )


QUANTILE_CASES = [
    (ad.qnorm, (0.0, 1.0), {}), (ad.qunif, (-2.0, 3.0), {}),
    (ad.qgamma, (2.0,), {}), (ad.qbeta, (2.0, 3.0), {}),
    (ad.qlnorm, (0.0, 1.0), {}), (ad.qchisq, (5.0,), {}),
    (ad.qf, (5.0, 9.0), {}), (ad.qt, (7.0,), {}),
    (ad.qbinom, (20.0, 0.3), {}), (ad.qcauchy, (0.0, 1.0), {}),
    (ad.qexp, (2.0,), {}), (ad.qgeom, (0.3,), {}),
    (ad.qhyper, (7.0, 13.0, 5.0), {}), (ad.qnbinom, (5.0, 0.4), {}),
    (ad.qpois, (4.0,), {}), (ad.qweibull, (1.5, 2.0), {}),
    (ad.qlogis, (0.0, 1.0), {}), (ad.qwilcox, (5.0, 6.0), {}),
    (ad.qsignrank, (8.0,), {}), (ad.qtukey, (5.0, 20.0, 1.0), {}),
    (ad.qbeta, (2.0, 3.0), {"ncp": 1.5}),
    (ad.qchisq, (5.0,), {"ncp": 1.5}),
    (ad.qf, (5.0, 9.0), {"ncp": 1.5}), (ad.qt, (7.0,), {"ncp": 1.5}),
]


@pytest.mark.parametrize(("quantile", "parameters", "kwargs"), QUANTILE_CASES)
def test_every_quantile_has_consistent_tail_and_log_probability_forms(quantile, parameters, kwargs):
    for probability in (0.125, 0.25, 0.5, 0.75, 0.875):
        lower = quantile(probability, *parameters, **kwargs)
        upper = quantile(1.0 - probability, *parameters, lower_tail=False, **kwargs)
        logged = quantile(np.log(probability), *parameters, log=True, **kwargs)
        assert lower == pytest.approx(upper, rel=1e-12, abs=1e-12)
        assert lower == pytest.approx(logged, rel=1e-12, abs=1e-12)


@pytest.mark.parametrize(
    ("density", "support", "parameters"),
    [
        (ad.dbinom, range(21), (20.0, 0.3)),
        (ad.dhyper, range(6), (7.0, 13.0, 5.0)),
        (ad.dwilcox, range(31), (5.0, 6.0)),
        (ad.dsignrank, range(37), (8.0,)),
    ],
)
def test_every_finite_discrete_density_sums_to_one(density, support, parameters):
    assert sum(float(density(x, *parameters)) for x in support) == pytest.approx(1.0, rel=1e-14)
