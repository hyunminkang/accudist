"""Shared machinery for the deliberately partial scipy.stats facade."""

from __future__ import annotations

import functools


_UNIMPLEMENTED = {
    "fit", "expect", "moment", "stats", "entropy", "interval", "median",
    "mean", "var", "std", "nnlf", "support",
}


class _Frozen:
    def __init__(self, distribution, args, kwargs):
        self._distribution = distribution
        self._args = args
        self._kwargs = kwargs

    def __getattr__(self, name):
        method = getattr(self._distribution, name)
        if name == "rvs":
            return functools.partial(method, *self._args, **self._kwargs)

        def frozen(value, **kwargs):
            merged = {**self._kwargs, **kwargs}
            return method(value, *self._args, **merged)

        return frozen


class _Dist:
    def __call__(self, *args, **kwargs):
        return _Frozen(self, args, kwargs)

    def __getattr__(self, name):
        if name in _UNIMPLEMENTED:
            raise NotImplementedError(
                f"{name} is outside accudist.compat; use the flat accudist API "
                "for precision functions or scipy.stats for summary/statistical methods"
            )
        raise AttributeError(name)

