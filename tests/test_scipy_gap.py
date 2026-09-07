"""Layer 3: the cases that motivate the package -- scipy underflows, R does not.

The scipy assertions are deliberate: when scipy fixes one of these, the test
fails and tells us to move the case to the 'scipy is now fine' table in the docs.
"""

import numpy as np
import pytest

import accudist as ad

scipy_stats = pytest.importorskip("scipy.stats")

pytestmark = pytest.mark.scipy_gap


def test_poisson_upper_log_tail():
    assert ad.ppois(200, 0.1, lower_tail=False, log=True) == pytest.approx(-1331.454400, abs=1e-5)
    assert np.isneginf(scipy_stats.poisson.logsf(200, 0.1))


def test_binomial_upper_log_tail():
    assert ad.pbinom(900, 1000, 1 / 6, lower_tail=False, log=True) == pytest.approx(-1312.687973, abs=1e-5)
    assert np.isneginf(scipy_stats.binom.logsf(900, 1000, 1 / 6))


def test_gamma_upper_log_tail():
    assert ad.pgamma(1e5, 2, lower_tail=False, log=True) == pytest.approx(-99988.48706, abs=1e-4)
    assert np.isneginf(scipy_stats.gamma.logsf(1e5, 2))


def test_negative_binomial_upper_log_tail():
    assert ad.pnbinom(1e5, 10, 0.5, lower_tail=False, log=True) == pytest.approx(-69230.83, abs=1e-1)
    assert np.isneginf(scipy_stats.nbinom.logsf(1e5, 10, 0.5))


def test_quantile_from_log_probability():
    assert ad.qnorm(-1000, log=True) == pytest.approx(-44.61574773, abs=1e-7)
    assert ad.qbeta(-1000, 0.5, 0.5, log=True) == pytest.approx(1.1125e-308, rel=1e-3)
    assert scipy_stats.beta.ppf(np.exp(-1000.0), 0.5, 0.5) == 0.0


def test_where_scipy_is_accurate_we_agree():
    for x in (-3.0, -1.0, 0.5, 2.5):
        assert ad.pnorm(x) == pytest.approx(scipy_stats.norm.cdf(x), rel=1e-13)
        assert ad.qnorm(ad.pnorm(x)) == pytest.approx(x, rel=1e-12)
    assert ad.pgamma(3.0, 2.5, scale=2.0) == pytest.approx(scipy_stats.gamma.cdf(3.0, 2.5, scale=2.0), rel=1e-13)
    assert ad.pbinom(7, 20, 0.3) == pytest.approx(scipy_stats.binom.cdf(7, 20, 0.3), rel=1e-13)
