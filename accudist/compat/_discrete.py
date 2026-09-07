"""Discrete distributions of the scipy-shaped shim."""

from __future__ import annotations

import numpy as np

import accudist as ad
from ._base import Dist, Spec

binom = Dist(Spec(
    "binom", ("n", "p"), True,
    d=lambda k, n, p, **f: ad.dbinom(k, n, p, **f),
    p=lambda k, n, p, **f: ad.pbinom(k, n, p, **f),
    q=lambda q, n, p, **f: ad.qbinom(q, n, p, **f),
    r=lambda size, n, p: ad.rbinom(size, n, p),
    r_family="binom",
))

poisson = Dist(Spec(
    "poisson", ("mu",), True,
    d=lambda k, mu, **f: ad.dpois(k, mu, **f),
    p=lambda k, mu, **f: ad.ppois(k, mu, **f),
    q=lambda q, mu, **f: ad.qpois(q, mu, **f),
    r=lambda size, mu: ad.rpois(size, mu),
    r_family="pois",
))

nbinom = Dist(Spec(
    "nbinom", ("n", "p"), True,
    d=lambda k, n, p, **f: ad.dnbinom(k, n, p, **f),
    p=lambda k, n, p, **f: ad.pnbinom(k, n, p, **f),
    q=lambda q, n, p, **f: ad.qnbinom(q, n, p, **f),
    r=lambda size, n, p: ad.rnbinom(size, n, p),
    r_family="nbinom",
))

# scipy's geometric distribution counts trials (support {1, 2, ...}); R's counts
# failures before the first success (support {0, 1, ...}).
geom = Dist(Spec(
    "geom", ("p",), True,
    d=lambda k, p, **f: ad.dgeom(np.subtract(k, 1), p, **f),
    p=lambda k, p, **f: ad.pgeom(np.subtract(k, 1), p, **f),
    q=lambda q, p, **f: np.add(ad.qgeom(q, p, **f), 1),
    r=lambda size, p: ad.rgeom(size, p) + 1,
    r_family="geom",
))

# scipy: hypergeom(M, n, N) = (population, successes in population, draws)
# R:     *hyper(m, n, k)     = (white balls, black balls, balls drawn)
hypergeom = Dist(Spec(
    "hypergeom", ("M", "n", "N"), True,
    d=lambda k, M, n, N, **f: ad.dhyper(k, n, np.subtract(M, n), N, **f),
    p=lambda k, M, n, N, **f: ad.phyper(k, n, np.subtract(M, n), N, **f),
    q=lambda q, M, n, N, **f: ad.qhyper(q, n, np.subtract(M, n), N, **f),
    r=lambda size, M, n, N: ad.rhyper(size, n, np.subtract(M, n), N),
    r_family="hyper",
))

__all__ = ["binom", "poisson", "nbinom", "geom", "hypergeom"]
