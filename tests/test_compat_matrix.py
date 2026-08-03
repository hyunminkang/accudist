import numpy as np
import pytest
import scipy.stats as stats

from accudist import compat


CONTINUOUS = [
    ("norm", (), 1.2),
    ("gamma", (2.0,), 1.2),
    ("beta", (2.0, 3.0), 1.2),
    ("chi2", (5.0,), 1.2),
    ("t", (7.0,), 1.2),
    ("f", (5.0, 9.0), 1.2),
    ("expon", (), 1.2),
    ("weibull_min", (1.5,), 1.2),
    ("lognorm", (0.8,), 1.2),
    ("cauchy", (), 1.2),
    ("logistic", (), 1.2),
    ("uniform", (), 1.2),
]
DISCRETE = [
    ("binom", (10, 0.3), 4),
    ("poisson", (3.0,), 4),
    ("nbinom", (5, 0.4), 4),
    ("geom", (0.3,), 4),
    ("hypergeom", (20, 7, 5), 3),
]


@pytest.mark.parametrize(("name", "shapes", "x"), CONTINUOUS)
def test_all_continuous_methods_agree_frozen_and_unfrozen(name, shapes, x):
    ours = getattr(compat, name)
    theirs = getattr(stats, name)
    options = {"loc": 0.3, "scale": 1.7}
    for method in ("pdf", "logpdf", "cdf", "logcdf", "sf", "logsf"):
        expected = getattr(theirs, method)(x, *shapes, **options)
        assert getattr(ours, method)(x, *shapes, **options) == pytest.approx(expected, rel=1e-12)
        assert getattr(ours(*shapes, **options), method)(x) == pytest.approx(expected, rel=1e-12)
    for method in ("ppf", "isf"):
        expected = getattr(theirs, method)(0.4, *shapes, **options)
        assert getattr(ours, method)(0.4, *shapes, **options) == pytest.approx(expected, rel=1e-12)
        assert getattr(ours(*shapes, **options), method)(0.4) == pytest.approx(expected, rel=1e-12)
    assert ours.rvs(*shapes, **options, size=4).shape == (4,)
    assert ours(*shapes, **options).rvs(size=4).shape == (4,)


@pytest.mark.parametrize(("name", "shapes", "x"), DISCRETE)
def test_all_discrete_methods_agree_frozen_and_unfrozen(name, shapes, x):
    ours = getattr(compat, name)
    theirs = getattr(stats, name)
    options = {"loc": 2}
    for method in ("pmf", "logpmf", "cdf", "logcdf", "sf", "logsf"):
        expected = getattr(theirs, method)(x, *shapes, **options)
        assert getattr(ours, method)(x, *shapes, **options) == pytest.approx(expected, rel=1e-12)
        assert getattr(ours(*shapes, **options), method)(x) == pytest.approx(expected, rel=1e-12)
    for method in ("ppf", "isf"):
        expected = getattr(theirs, method)(0.4, *shapes, **options)
        assert getattr(ours, method)(0.4, *shapes, **options) == expected
        assert getattr(ours(*shapes, **options), method)(0.4) == expected
    assert ours.rvs(*shapes, **options, size=4).shape == (4,)
    assert ours(*shapes, **options).rvs(size=4).shape == (4,)


@pytest.mark.parametrize("name", [item[0] for item in CONTINUOUS + DISCRETE])
def test_every_unsupported_method_has_actionable_message(name):
    distribution = getattr(compat, name)
    for method in ("fit", "expect", "moment", "stats", "entropy", "interval", "median", "mean", "var", "std", "nnlf", "support"):
        with pytest.raises(NotImplementedError, match="flat accudist API.*scipy.stats"):
            getattr(distribution, method)
