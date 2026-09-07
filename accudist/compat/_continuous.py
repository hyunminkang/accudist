"""Continuous distributions of the scipy-shaped shim.

Each is expressed on the standardised variable ``y = (x - loc) / scale`` with
R's default location/scale, so ``loc``/``scale`` handling (including the
density Jacobian) lives once in ``_base``.
"""

from __future__ import annotations

import accudist as ad
from ._base import Dist, Spec

norm = Dist(Spec(
    "norm", (), False,
    d=lambda y, **f: ad.dnorm(y, **f), p=lambda y, **f: ad.pnorm(y, **f),
    q=lambda q, **f: ad.qnorm(q, **f), r=lambda n: ad.rnorm(n), r_family="norm",
))

gamma = Dist(Spec(
    "gamma", ("a",), False,
    d=lambda y, a, **f: ad.dgamma(y, a, scale=1.0, **f), p=lambda y, a, **f: ad.pgamma(y, a, scale=1.0, **f),
    q=lambda q, a, **f: ad.qgamma(q, a, scale=1.0, **f), r=lambda n, a: ad.rgamma(n, a, scale=1.0), r_family="gamma",
))

beta = Dist(Spec(
    "beta", ("a", "b"), False,
    d=lambda y, a, b, **f: ad.dbeta(y, a, b, **f), p=lambda y, a, b, **f: ad.pbeta(y, a, b, **f),
    q=lambda q, a, b, **f: ad.qbeta(q, a, b, **f), r=lambda n, a, b: ad.rbeta(n, a, b), r_family="beta",
))

chi2 = Dist(Spec(
    "chi2", ("df",), False,
    d=lambda y, df, **f: ad.dchisq(y, df, **f), p=lambda y, df, **f: ad.pchisq(y, df, **f),
    q=lambda q, df, **f: ad.qchisq(q, df, **f), r=lambda n, df: ad.rchisq(n, df), r_family="chisq",
))

t = Dist(Spec(
    "t", ("df",), False,
    d=lambda y, df, **f: ad.dt(y, df, **f), p=lambda y, df, **f: ad.pt(y, df, **f),
    q=lambda q, df, **f: ad.qt(q, df, **f), r=lambda n, df: ad.rt(n, df), r_family="t",
))

f = Dist(Spec(
    "f", ("dfn", "dfd"), False,
    d=lambda y, dfn, dfd, **fl: ad.df(y, dfn, dfd, **fl), p=lambda y, dfn, dfd, **fl: ad.pf(y, dfn, dfd, **fl),
    q=lambda q, dfn, dfd, **fl: ad.qf(q, dfn, dfd, **fl), r=lambda n, dfn, dfd: ad.rf(n, dfn, dfd), r_family="f",
))

expon = Dist(Spec(
    "expon", (), False,
    d=lambda y, **fl: ad.dexp(y, 1.0, **fl), p=lambda y, **fl: ad.pexp(y, 1.0, **fl),
    q=lambda q, **fl: ad.qexp(q, 1.0, **fl), r=lambda n: ad.rexp(n, 1.0), r_family="exp",
))

weibull_min = Dist(Spec(
    "weibull_min", ("c",), False,
    d=lambda y, c, **fl: ad.dweibull(y, c, 1.0, **fl), p=lambda y, c, **fl: ad.pweibull(y, c, 1.0, **fl),
    q=lambda q, c, **fl: ad.qweibull(q, c, 1.0, **fl), r=lambda n, c: ad.rweibull(n, c, 1.0), r_family="weibull",
))

# scipy's lognorm(s, loc, scale): scale = exp(meanlog); standardising by scale
# gives plnorm(y, meanlog = 0, sdlog = s).
lognorm = Dist(Spec(
    "lognorm", ("s",), False,
    d=lambda y, s, **fl: ad.dlnorm(y, 0.0, s, **fl), p=lambda y, s, **fl: ad.plnorm(y, 0.0, s, **fl),
    q=lambda q, s, **fl: ad.qlnorm(q, 0.0, s, **fl), r=lambda n, s: ad.rlnorm(n, 0.0, s), r_family="lnorm",
))

cauchy = Dist(Spec(
    "cauchy", (), False,
    d=lambda y, **fl: ad.dcauchy(y, **fl), p=lambda y, **fl: ad.pcauchy(y, **fl),
    q=lambda q, **fl: ad.qcauchy(q, **fl), r=lambda n: ad.rcauchy(n), r_family="cauchy",
))

logistic = Dist(Spec(
    "logistic", (), False,
    d=lambda y, **fl: ad.dlogis(y, **fl), p=lambda y, **fl: ad.plogis(y, **fl),
    q=lambda q, **fl: ad.qlogis(q, **fl), r=lambda n: ad.rlogis(n), r_family="logis",
))

uniform = Dist(Spec(
    "uniform", (), False,
    d=lambda y, **fl: ad.dunif(y, **fl), p=lambda y, **fl: ad.punif(y, **fl),
    q=lambda q, **fl: ad.qunif(q, **fl), r=lambda n: ad.runif(n), r_family="unif",
))

__all__ = ["norm", "gamma", "beta", "chi2", "t", "f", "expon", "weibull_min", "lognorm", "cauchy", "logistic", "uniform"]
