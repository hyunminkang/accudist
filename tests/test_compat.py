"""The scipy-shaped shim: agreement where scipy is accurate, improvement where it is not."""

import numpy as np
import pytest

import accudist as ad
from accudist import compat

stats = pytest.importorskip("scipy.stats")

RTOL = 1e-12

CASES = [
    # (accudist dist, scipy dist, shape args, kwargs, x values, probabilities)
    (compat.binom, stats.binom, (20, 0.3), {}, [0, 3, 7, 20], [0.01, 0.5, 0.9]),
    (compat.binom, stats.binom, (20, 0.3), {"loc": 2}, [2, 5, 9], [0.01, 0.5, 0.9]),
    (compat.poisson, stats.poisson, (4.5,), {}, [0, 2, 8], [0.05, 0.5, 0.95]),
    (compat.nbinom, stats.nbinom, (5, 0.4), {}, [0, 3, 12], [0.05, 0.5, 0.95]),
    (compat.geom, stats.geom, (0.3,), {}, [1, 2, 5], [0.05, 0.5, 0.95]),
    (compat.hypergeom, stats.hypergeom, (20, 7, 12), {}, [1, 4, 7], [0.05, 0.5, 0.95]),
    (compat.norm, stats.norm, (), {"loc": 1.5, "scale": 2.0}, [-2.0, 1.5, 4.0], [0.01, 0.5, 0.99]),
    (compat.gamma, stats.gamma, (2.5,), {"loc": 1.0, "scale": 3.0}, [1.5, 4.0, 20.0], [0.01, 0.5, 0.99]),
    (compat.beta, stats.beta, (2.0, 5.0), {}, [0.1, 0.4, 0.9], [0.01, 0.5, 0.99]),
    (compat.chi2, stats.chi2, (4.0,), {"scale": 2.0}, [0.5, 4.0, 20.0], [0.01, 0.5, 0.99]),
    (compat.t, stats.t, (5.0,), {"loc": -1.0}, [-3.0, 0.0, 2.0], [0.01, 0.5, 0.99]),
    (compat.f, stats.f, (3.0, 8.0), {}, [0.3, 1.0, 4.0], [0.01, 0.5, 0.99]),
    (compat.expon, stats.expon, (), {"scale": 0.5}, [0.1, 0.5, 3.0], [0.01, 0.5, 0.99]),
    (compat.weibull_min, stats.weibull_min, (1.7,), {"scale": 2.0}, [0.3, 2.0, 5.0], [0.01, 0.5, 0.99]),
    (compat.lognorm, stats.lognorm, (0.8,), {"scale": 3.0}, [0.5, 3.0, 10.0], [0.01, 0.5, 0.99]),
    (compat.cauchy, stats.cauchy, (), {"loc": 1.0, "scale": 0.5}, [-3.0, 1.0, 5.0], [0.01, 0.5, 0.99]),
    (compat.logistic, stats.logistic, (), {"loc": 1.0, "scale": 0.5}, [-3.0, 1.0, 5.0], [0.01, 0.5, 0.99]),
    (compat.uniform, stats.uniform, (), {"loc": -1.0, "scale": 3.0}, [-0.5, 0.0, 1.9], [0.01, 0.5, 0.99]),
]


@pytest.mark.parametrize("ours, theirs, shapes, kw, xs, ps", CASES, ids=lambda v: getattr(v, "name", None) or "")
def test_agreement_with_scipy_where_scipy_is_accurate(ours, theirs, shapes, kw, xs, ps):
    dens = "pmf" if ours._spec.discrete else "pdf"
    for x in xs:
        for method in (dens, f"log{dens}", "cdf", "logcdf", "sf", "logsf"):
            got = getattr(ours, method)(x, *shapes, **kw)
            want = getattr(theirs, method)(x, *shapes, **kw)
            assert got == pytest.approx(want, rel=RTOL, abs=1e-300), (method, x)
            frozen = getattr(ours(*shapes, **kw), method)(x)
            assert frozen == got
    for p in ps:
        for method in ("ppf", "isf"):
            got = getattr(ours, method)(p, *shapes, **kw)
            want = getattr(theirs, method)(p, *shapes, **kw)
            assert got == pytest.approx(want, rel=1e-9, abs=1e-12), (method, p)


def test_improvement_on_the_gap_cases():
    assert compat.binom.logsf(900, 1000, 1 / 6) == pytest.approx(-1312.687973, abs=1e-5)
    assert np.isneginf(stats.binom.logsf(900, 1000, 1 / 6))
    assert compat.poisson(0.1).logsf(200) == pytest.approx(-1331.454400, abs=1e-5)
    assert compat.gamma.logsf(1e5, 2) == pytest.approx(-99988.48706, abs=1e-4)
    assert compat.nbinom.logsf(1e5, 10, 0.5) == pytest.approx(-69230.83, abs=0.1)


def test_geom_off_by_one():
    assert compat.geom.pmf(1, 0.3) == pytest.approx(0.3)
    assert compat.geom.pmf(0, 0.3) == 0.0
    assert compat.geom.ppf(0.5, 0.3) == stats.geom.ppf(0.5, 0.3)
    assert np.all(compat.geom.rvs(0.3, size=100) >= 1)


def test_hypergeom_reparameterisation():
    assert compat.hypergeom.pmf(4, 20, 7, 12) == pytest.approx(stats.hypergeom.pmf(4, 20, 7, 12), rel=RTOL)
    assert compat.hypergeom.pmf(4, 20, 7, 12) == pytest.approx(ad.dhyper(4, 7, 13, 12), rel=RTOL)


def test_lognorm_scale_is_exp_meanlog():
    assert compat.lognorm.cdf(3.0, 0.8, scale=np.exp(1.2)) == pytest.approx(ad.plnorm(3.0, 1.2, 0.8), rel=RTOL)


def test_logpdf_jacobian():
    assert compat.norm.logpdf(1.0, loc=0.0, scale=4.0) == pytest.approx(ad.dnorm(0.25, log=True) - np.log(4.0), rel=RTOL)
    assert compat.gamma.pdf(2.0, 3.0, scale=0.5) == pytest.approx(stats.gamma.pdf(2.0, 3.0, scale=0.5), rel=RTOL)


def test_rvs_shapes_and_fit():
    ad.set_seed(1, 2)
    x = compat.gamma.rvs(2.0, scale=3.0, size=(4, 5))
    assert x.shape == (4, 5)
    assert isinstance(compat.norm.rvs(), np.floating)
    y = compat.norm(10.0, 0.1).rvs(size=2000)
    assert abs(y.mean() - 10.0) < 0.02
    k = compat.binom(5, 0.5, loc=3).rvs(size=50)
    assert np.all((k >= 3) & (k <= 8))


def test_absent_methods_raise_with_pointer():
    for method in ("fit", "mean", "var", "entropy", "moment", "interval", "median", "stats"):
        with pytest.raises(NotImplementedError) as info:
            getattr(compat.binom, method)
        assert "accudist.pbinom" in str(info.value) and f"scipy.stats.binom.{method}" in str(info.value)
        with pytest.raises(NotImplementedError):
            getattr(compat.norm(0, 1), method)
    with pytest.raises(AttributeError):
        compat.norm.no_such_thing


def test_parameter_errors():
    with pytest.raises(TypeError, match="missing shape"):
        compat.binom.cdf(3)
    with pytest.raises(TypeError, match="unexpected"):
        compat.norm.cdf(0.0, shape=2)
    with pytest.raises(TypeError, match="at most"):
        compat.norm.cdf(0.0, 1, 2, 3)
