import numpy as np
import pytest
from scipy import stats

from accudist import compat


@pytest.mark.parametrize(
    ("ours", "theirs", "args", "x"),
    [
        (compat.binom, stats.binom, (12, 0.3), 4),
        (compat.poisson, stats.poisson, (3.5,), 5),
        (compat.geom, stats.geom, (0.35,), 4),
        (compat.hypergeom, stats.hypergeom, (30, 8, 6), 3),
        (compat.norm, stats.norm, (), 1.2),
        (compat.gamma, stats.gamma, (2.5,), 3.0),
        (compat.beta, stats.beta, (2.0, 5.0), 0.35),
        (compat.lognorm, stats.lognorm, (0.8,), 2.0),
    ],
)
def test_compat_cdf_and_density_agree_with_scipy(ours, theirs, args, x):
    kwargs = {"loc": 0.4, "scale": 1.7} if ours in {compat.norm, compat.gamma, compat.beta, compat.lognorm} else {"loc": 2}
    np.testing.assert_allclose(ours.cdf(x, *args, **kwargs), theirs.cdf(x, *args, **kwargs), rtol=1e-12)
    density = "pmf" if hasattr(theirs, "pmf") else "pdf"
    np.testing.assert_allclose(getattr(ours, density)(x, *args, **kwargs), getattr(theirs, density)(x, *args, **kwargs), rtol=1e-12)


def test_frozen_and_unfrozen_forms_match():
    frozen = compat.binom(1000, 1 / 6)
    assert frozen.logsf(900) == compat.binom.logsf(900, 1000, 1 / 6)
    assert np.isfinite(frozen.logsf(900))


def test_geom_hypergeom_and_lognorm_parameterization_traps():
    assert compat.geom.pmf(1, 0.25) == pytest.approx(stats.geom.pmf(1, 0.25))
    assert compat.hypergeom.cdf(3, 40, 9, 7) == pytest.approx(stats.hypergeom.cdf(3, 40, 9, 7))
    assert compat.lognorm.cdf(3, 0.7, scale=2.5) == pytest.approx(stats.lognorm.cdf(3, 0.7, scale=2.5))


def test_unimplemented_methods_name_both_alternatives():
    with pytest.raises(NotImplementedError, match="flat accudist API.*scipy"):
        compat.norm.mean()


@pytest.mark.scipy_gap
@pytest.mark.parametrize(
    ("distribution", "args", "x"),
    [
        (compat.binom, (1000, 1 / 6), 900),
        (compat.poisson, (0.1,), 200),
        (compat.nbinom, (10, 0.5), 1e5),
        (compat.gamma, (2,), 1e5),
        (compat.chi2, (3,), 1e5),
        (compat.f, (3, 7), 1e300),
    ],
)
def test_compat_logsf_preserves_the_supported_scipy_gap_improvements(distribution, args, x):
    assert np.isfinite(distribution.logsf(x, *args))
