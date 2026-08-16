import numpy as np
import pytest
from scipy import stats

import accudist as ad


@pytest.mark.scipy_gap
@pytest.mark.parametrize(
    ("ours", "scipy_value", "expected"),
    [
        (lambda: ad.pbinom(900, 1000, 1 / 6, lower_tail=False, log=True), lambda: stats.binom.logsf(900, 1000, 1 / 6), -1312.687973),
        (lambda: ad.ppois(200, 0.1, lower_tail=False, log=True), lambda: stats.poisson.logsf(200, 0.1), -1331.454401),
        (lambda: ad.ppois(1000, 1, lower_tail=False, log=True), lambda: stats.poisson.logsf(1000, 1), -5920.035935),
        (lambda: ad.pnbinom(1e5, 10, 0.5, lower_tail=False, log=True), lambda: stats.nbinom.logsf(1e5, 10, 0.5), -69230.8344),
        (lambda: ad.pgamma(1e5, 2, lower_tail=False, log=True), lambda: stats.gamma.logsf(1e5, 2), -99988.48706),
        (lambda: ad.pchisq(1e5, 3, lower_tail=False, log=True), lambda: stats.chi2.logsf(1e5, 3), -49994.46932),
        (lambda: ad.pf(1e300, 3, 7, lower_tail=False, log=True), lambda: stats.f.logsf(1e300, 3, 7), -2413.903706),
    ],
)
def test_upper_log_tail_remains_finite_where_scipy_underflows(ours, scipy_value, expected):
    assert ours() == pytest.approx(expected, abs=1e-5)
    assert np.isneginf(scipy_value())


@pytest.mark.scipy_gap
@pytest.mark.parametrize(
    ("ours", "scipy_value", "expected"),
    [
        (lambda: ad.qnorm(-1000, log=True), lambda: stats.norm.ppf(np.exp(-1000)), -44.61574773),
        (lambda: ad.qgamma(-1000, 2, log=True), lambda: stats.gamma.ppf(np.exp(-1000), 2), 1.007567258e-217),
        (lambda: ad.qbeta(-1000, 0.5, 0.5, log=True), lambda: stats.beta.ppf(np.exp(-1000), 0.5, 0.5), 1.112536929e-308),
        (lambda: ad.qt(-700, 5, log=True), lambda: stats.t.ppf(np.exp(-700), 5), -9.923896826e60),
    ],
)
def test_log_probability_quantiles_retain_accuracy_where_scipy_does_not(
    ours, scipy_value, expected
):
    assert ours() == pytest.approx(expected, rel=1e-9, abs=0)
    assert scipy_value() != pytest.approx(expected, rel=1e-9, abs=0)


@pytest.mark.scipy_gap
@pytest.mark.parametrize(
    ("ours", "expected"),
    [
        (lambda: ad.ptukey(10, 5, 20, lower_tail=False, log=True), -11.90476371),
        (lambda: ad.pwilcox(390, 20, 20, lower_tail=False, log=True), -21.07469581),
        (lambda: ad.psignrank(460, 30, lower_tail=False, log=True), -18.84850527),
    ],
)
def test_rmath_only_gap_functions(ours, expected):
    assert ours() == pytest.approx(expected, abs=1e-7)
