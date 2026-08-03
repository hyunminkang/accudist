"""Continuous scipy-shaped distributions backed by the public accudist API."""

from __future__ import annotations

import numpy as np

import accudist as ad

from ._base import _Dist


class _Continuous(_Dist):
    def __init__(self, name):
        self.name = name

    @property
    def _family(self):
        return {"chi2": "chisq", "expon": "exp", "weibull_min": "weibull", "lognorm": "lnorm", "logistic": "logis", "uniform": "unif"}.get(self.name, self.name)

    def _mapping(self, value, shapes, loc, scale):
        if scale <= 0:
            raise ValueError("scale must be positive")
        if self.name == "norm":
            return value, {"mean": loc, "sd": scale}, False, lambda q: q
        if self.name == "gamma":
            (a,) = shapes
            return value - loc, {"shape": a, "scale": scale}, False, lambda q: q + loc
        if self.name == "beta":
            a, b = shapes
            return (value - loc) / scale, {"shape1": a, "shape2": b}, True, lambda q: loc + scale * q
        if self.name == "chi2":
            (df,) = shapes
            return (value - loc) / scale, {"df": df}, True, lambda q: loc + scale * q
        if self.name == "t":
            (df,) = shapes
            return (value - loc) / scale, {"df": df}, True, lambda q: loc + scale * q
        if self.name == "f":
            dfn, dfd = shapes
            return (value - loc) / scale, {"df1": dfn, "df2": dfd}, True, lambda q: loc + scale * q
        if self.name == "expon":
            return value - loc, {"rate": 1.0 / scale}, False, lambda q: q + loc
        if self.name == "weibull_min":
            (shape,) = shapes
            return (value - loc) / scale, {"shape": shape, "scale": 1.0}, True, lambda q: loc + scale * q
        if self.name == "lognorm":
            (s,) = shapes
            return value - loc, {"meanlog": np.log(scale), "sdlog": s}, False, lambda q: q + loc
        if self.name == "cauchy":
            return value, {"location": loc, "scale": scale}, False, lambda q: q
        if self.name == "logistic":
            return value, {"location": loc, "scale": scale}, False, lambda q: q
        if self.name == "uniform":
            return value, {"min": loc, "max": loc + scale}, False, lambda q: q
        raise AssertionError(self.name)

    def _density(self, value, shapes, loc, scale, log):
        transformed, parameters, jacobian, _ = self._mapping(value, shapes, loc, scale)
        result = getattr(ad, "d" + self._family)(transformed, **parameters, log=log)
        if jacobian:
            return result - np.log(scale) if log else result / scale
        return result

    def pdf(self, x, *shapes, loc=0, scale=1):
        return self._density(x, shapes, loc, scale, False)

    def logpdf(self, x, *shapes, loc=0, scale=1):
        return self._density(x, shapes, loc, scale, True)

    def _probability(self, x, shapes, loc, scale, lower_tail, log):
        transformed, parameters, _, _ = self._mapping(x, shapes, loc, scale)
        return getattr(ad, "p" + self._family)(transformed, **parameters, lower_tail=lower_tail, log=log)

    def cdf(self, x, *shapes, loc=0, scale=1):
        return self._probability(x, shapes, loc, scale, True, False)

    def logcdf(self, x, *shapes, loc=0, scale=1):
        return self._probability(x, shapes, loc, scale, True, True)

    def sf(self, x, *shapes, loc=0, scale=1):
        return self._probability(x, shapes, loc, scale, False, False)

    def logsf(self, x, *shapes, loc=0, scale=1):
        return self._probability(x, shapes, loc, scale, False, True)

    def _quantile(self, probability, shapes, loc, scale, lower_tail):
        _, parameters, _, reverse = self._mapping(0.0, shapes, loc, scale)
        value = getattr(ad, "q" + self._family)(probability, **parameters, lower_tail=lower_tail)
        return reverse(value)

    def ppf(self, probability, *shapes, loc=0, scale=1):
        return self._quantile(probability, shapes, loc, scale, True)

    def isf(self, probability, *shapes, loc=0, scale=1):
        return self._quantile(probability, shapes, loc, scale, False)

    def rvs(self, *shapes, loc=0, scale=1, size=1, random_state=None):
        if random_state is not None:
            raise NotImplementedError("random_state has no exact mapping; use accudist.RNG")
        _, parameters, _, reverse = self._mapping(0.0, shapes, loc, scale)
        value = getattr(ad, "r" + self._family)(size, **parameters)
        return reverse(value)


norm = _Continuous("norm")
gamma = _Continuous("gamma")
beta = _Continuous("beta")
chi2 = _Continuous("chi2")
t = _Continuous("t")
f = _Continuous("f")
expon = _Continuous("expon")
weibull_min = _Continuous("weibull_min")
lognorm = _Continuous("lognorm")
cauchy = _Continuous("cauchy")
logistic = _Continuous("logistic")
uniform = _Continuous("uniform")
