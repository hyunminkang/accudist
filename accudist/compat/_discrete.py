"""Discrete scipy-shaped distributions backed by the public accudist API."""

from __future__ import annotations

import accudist as ad

from ._base import _Dist


class _Discrete(_Dist):
    def __init__(self, name):
        self.name = name

    def _parameters(self, shapes):
        if self.name == "binom":
            n, p = shapes
            return {"size": n, "prob": p}
        if self.name == "poisson":
            (mu,) = shapes
            return {"lambda_": mu}
        if self.name == "nbinom":
            n, p = shapes
            return {"size": n, "prob": p}
        if self.name == "geom":
            (p,) = shapes
            return {"prob": p}
        if self.name == "hypergeom":
            population, successes, draws = shapes
            return {"m": successes, "n": population - successes, "k": draws}
        raise AssertionError(self.name)

    def _x(self, value, loc):
        return value - loc - (1 if self.name == "geom" else 0)

    def _from_quantile(self, value, loc):
        return value + loc + (1 if self.name == "geom" else 0)

    @property
    def _family(self):
        return {"poisson": "pois", "hypergeom": "hyper"}.get(self.name, self.name)

    def pmf(self, k, *shapes, loc=0):
        return getattr(ad, "d" + self._family)(self._x(k, loc), **self._parameters(shapes))

    def logpmf(self, k, *shapes, loc=0):
        return getattr(ad, "d" + self._family)(self._x(k, loc), **self._parameters(shapes), log=True)

    def cdf(self, k, *shapes, loc=0):
        return getattr(ad, "p" + self._family)(self._x(k, loc), **self._parameters(shapes))

    def logcdf(self, k, *shapes, loc=0):
        return getattr(ad, "p" + self._family)(self._x(k, loc), **self._parameters(shapes), log=True)

    def sf(self, k, *shapes, loc=0):
        return getattr(ad, "p" + self._family)(self._x(k, loc), **self._parameters(shapes), lower_tail=False)

    def logsf(self, k, *shapes, loc=0):
        return getattr(ad, "p" + self._family)(self._x(k, loc), **self._parameters(shapes), lower_tail=False, log=True)

    def ppf(self, probability, *shapes, loc=0):
        value = getattr(ad, "q" + self._family)(probability, **self._parameters(shapes))
        return self._from_quantile(value, loc)

    def isf(self, probability, *shapes, loc=0):
        value = getattr(ad, "q" + self._family)(probability, **self._parameters(shapes), lower_tail=False)
        return self._from_quantile(value, loc)

    def rvs(self, *shapes, loc=0, size=1, random_state=None):
        if random_state is not None:
            raise NotImplementedError("random_state has no exact mapping; use accudist.RNG")
        value = getattr(ad, "r" + self._family)(size, **self._parameters(shapes))
        return self._from_quantile(value, loc)


binom = _Discrete("binom")
poisson = _Discrete("poisson")
nbinom = _Discrete("nbinom")
geom = _Discrete("geom")
hypergeom = _Discrete("hypergeom")

