"""A deliberately partial, tail-accurate facade for selected scipy.stats APIs."""

from ._continuous import beta, cauchy, chi2, expon, f, gamma, logistic, lognorm, norm, t, uniform, weibull_min
from ._discrete import binom, geom, hypergeom, nbinom, poisson

__all__ = [
    "binom", "poisson", "nbinom", "geom", "hypergeom", "norm", "gamma",
    "beta", "chi2", "t", "f", "expon", "weibull_min", "lognorm", "cauchy",
    "logistic", "uniform",
]

