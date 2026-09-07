"""Machinery for the scipy.stats-shaped shim.

A ``Dist`` takes scipy's parameters (shape parameters, then ``loc`` and, for
continuous distributions, ``scale``), standardises the argument, and calls the
public accudist function. Only the methods where tail precision matters exist;
everything else raises ``NotImplementedError`` pointing at the R-flat API.
"""

from __future__ import annotations

import math

import numpy as np

import accudist as ad

ABSENT = {
    "fit", "expect", "moment", "stats", "entropy", "interval", "median", "mean", "var",
    "std", "nnlf", "support", "logcdf_sf", "ppf_isf",
}

_MESSAGE = (
    "accudist.compat.{dist}.{method} is deliberately not implemented: the shim only covers "
    "the evaluation methods where tail precision matters (pmf/pdf, logpmf/logpdf, cdf, "
    "logcdf, sf, logsf, ppf, isf, rvs). Use the R-flat functions in `accudist` (e.g. "
    "`accudist.{rfunc}`) or `scipy.stats.{dist}.{method}`."
)


class Spec:
    """How one scipy distribution maps onto accudist.

    Parameters
    ----------
    name : scipy name
    shapes : scipy shape-parameter names, in scipy order
    discrete : True for pmf-type distributions (loc only, integer support)
    d, p, q, r : callables ``(y, *shapes, **flags)`` on the *standardised*
        variable ``y`` (``(x - loc) / scale`` or ``k - loc``) returning the
        accudist result; ``r`` is ``(n, *shapes)``.
    r_family : accudist family name, for error messages
    """

    def __init__(self, name, shapes, discrete, d, p, q, r, r_family):
        self.name = name
        self.shapes = tuple(shapes)
        self.discrete = discrete
        self.d, self.p, self.q, self.r = d, p, q, r
        self.r_family = r_family


class Dist:
    def __init__(self, spec: Spec):
        self._spec = spec
        self.name = spec.name
        self.__doc__ = f"scipy.stats.{spec.name}-shaped view of accudist's {spec.r_family} functions."

    # -- parameter handling -------------------------------------------------

    def _split(self, args, kwargs):
        spec = self._spec
        names = list(spec.shapes) + ["loc"] + ([] if spec.discrete else ["scale"])
        values = dict(zip(names, args))
        if len(args) > len(names):
            raise TypeError(f"{spec.name} takes at most {len(names)} parameters {names}, got {len(args)}")
        for k, v in kwargs.items():
            if k not in names:
                raise TypeError(f"{spec.name} got an unexpected parameter {k!r}; expected {names}")
            if k in values:
                raise TypeError(f"{spec.name} got multiple values for {k!r}")
            values[k] = v
        missing = [s for s in spec.shapes if s not in values]
        if missing:
            raise TypeError(f"{spec.name} is missing shape parameter(s) {missing}")
        shapes = tuple(values[s] for s in spec.shapes)
        loc = values.get("loc", 0)
        scale = values.get("scale", 1)
        return shapes, loc, scale

    def __call__(self, *args, **kwargs):
        shapes, loc, scale = self._split(args, kwargs)
        return Frozen(self, shapes, loc, scale)

    def __getattr__(self, method):
        if method in ABSENT:
            raise NotImplementedError(_MESSAGE.format(dist=self.name, method=method, rfunc=f"p{self._spec.r_family}"))
        raise AttributeError(method)

    # -- evaluation ---------------------------------------------------------

    def _y(self, x, loc, scale):
        if self._spec.discrete:
            return np.subtract(x, loc)
        return np.divide(np.subtract(x, loc), scale)

    def _pdf(self, x, shapes, loc, scale, log):
        spec = self._spec
        y = self._y(x, loc, scale)
        val = spec.d(y, *shapes, log=log)
        if spec.discrete:
            return val
        # Jacobian of the affine transform
        if log:
            return np.subtract(val, np.log(scale))
        return np.divide(val, scale)

    def _cdf(self, x, shapes, loc, scale, lower_tail, log):
        return self._spec.p(self._y(x, loc, scale), *shapes, lower_tail=lower_tail, log=log)

    def _ppf(self, prob, shapes, loc, scale, lower_tail):
        q = self._spec.q(prob, *shapes, lower_tail=lower_tail)
        if self._spec.discrete:
            return np.add(q, loc)
        return np.add(np.multiply(q, scale), loc)

    def _rvs(self, shapes, loc, scale, size):
        if size is None:
            n, shape = 1, ()
        elif isinstance(size, int):
            n, shape = size, (size,)
        else:
            shape = tuple(size)
            n = int(math.prod(shape))
        draws = self._spec.r(n, *shapes)
        draws = np.add(draws, loc) if self._spec.discrete else np.add(np.multiply(draws, scale), loc)
        return draws.reshape(shape) if shape else draws[0]

    # scipy-named methods; shape params may be positional or keyword

    def pmf(self, k, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._pdf(k, s, loc, sc, False)

    pdf = pmf

    def logpmf(self, k, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._pdf(k, s, loc, sc, True)

    logpdf = logpmf

    def cdf(self, x, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._cdf(x, s, loc, sc, True, False)

    def logcdf(self, x, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._cdf(x, s, loc, sc, True, True)

    def sf(self, x, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._cdf(x, s, loc, sc, False, False)

    def logsf(self, x, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._cdf(x, s, loc, sc, False, True)

    def ppf(self, q, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._ppf(q, s, loc, sc, True)

    def isf(self, q, *args, **kw):
        s, loc, sc = self._split(args, kw)
        return self._ppf(q, s, loc, sc, False)

    def rvs(self, *args, size=None, **kw):
        s, loc, sc = self._split(args, kw)
        return self._rvs(s, loc, sc, size)


class Frozen:
    def __init__(self, dist: Dist, shapes, loc, scale):
        self._dist, self._shapes, self._loc, self._scale = dist, shapes, loc, scale

    def __repr__(self):
        return f"accudist.compat.{self._dist.name}{(*self._shapes, self._loc, self._scale)!r}"

    def __getattr__(self, method):
        if method in ABSENT:
            raise NotImplementedError(_MESSAGE.format(dist=self._dist.name, method=method, rfunc=f"p{self._dist._spec.r_family}"))
        raise AttributeError(method)

    def pmf(self, k):
        return self._dist._pdf(k, self._shapes, self._loc, self._scale, False)

    pdf = pmf

    def logpmf(self, k):
        return self._dist._pdf(k, self._shapes, self._loc, self._scale, True)

    logpdf = logpmf

    def cdf(self, x):
        return self._dist._cdf(x, self._shapes, self._loc, self._scale, True, False)

    def logcdf(self, x):
        return self._dist._cdf(x, self._shapes, self._loc, self._scale, True, True)

    def sf(self, x):
        return self._dist._cdf(x, self._shapes, self._loc, self._scale, False, False)

    def logsf(self, x):
        return self._dist._cdf(x, self._shapes, self._loc, self._scale, False, True)

    def ppf(self, q):
        return self._dist._ppf(q, self._shapes, self._loc, self._scale, True)

    def isf(self, q):
        return self._dist._ppf(q, self._shapes, self._loc, self._scale, False)

    def rvs(self, size=None):
        return self._dist._rvs(self._shapes, self._loc, self._scale, size)
