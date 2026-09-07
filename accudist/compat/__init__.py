"""A deliberately partial ``scipy.stats``-shaped view of accudist.

    >>> from accudist.compat import binom
    >>> binom.logsf(900, 1000, 1/6)        # scipy: -inf
    -1312.6879734...
    >>> binom(1000, 1/6).logsf(900)        # frozen form

Distributions take **scipy's** parameters (``binom(n, p, loc)``,
``hypergeom(M, n, N)``, ``gamma(a, loc, scale)``, ...). Supported methods:
``pmf``/``pdf``, ``logpmf``/``logpdf``, ``cdf``, ``logcdf``, ``sf``, ``logsf``,
``ppf``, ``isf``, ``rvs``. ``sf``/``logsf``/``isf`` go through R's direct
upper-tail algorithms instead of ``1 - cdf``. Moments, fitting and the other
scipy conveniences are intentionally absent and raise ``NotImplementedError``.

``rvs`` draws from ``accudist.default_rng()`` (not scipy's or R's streams).
"""

from ._continuous import beta, cauchy, chi2, expon, f, gamma, logistic, lognorm, norm, t, uniform, weibull_min
from ._discrete import binom, geom, hypergeom, nbinom, poisson

__all__ = [
    "binom", "poisson", "nbinom", "geom", "hypergeom",
    "norm", "gamma", "beta", "chi2", "t", "f", "expon", "weibull_min", "lognorm", "cauchy", "logistic", "uniform",
]
