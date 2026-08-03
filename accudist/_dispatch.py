"""Argument-dispatch helpers used by generated public wrappers."""

from __future__ import annotations

import warnings

import numpy as np


def resolve_prob_mu(prob, mu) -> str:
    if (prob is None) == (mu is None):
        raise TypeError("exactly one of 'prob' or 'mu' must be specified")
    return "prob" if prob is not None else "mu"


def resolve_rate_scale(rate, scale):
    if rate is None and scale is None:
        return 1.0
    if rate is None:
        return scale
    inverse = reciprocal(rate)
    if scale is None:
        return inverse
    if not np.allclose(np.asarray(rate) * np.asarray(scale), 1.0, rtol=0.0, atol=1e-15):
        raise TypeError("inconsistent 'rate' and 'scale'; their product must be 1")
    warnings.warn("both 'rate' and 'scale' were specified consistently", UserWarning, stacklevel=3)
    return scale


def reciprocal(value):
    return np.reciprocal(np.asarray(value, dtype=np.float64))


def sqrt(value):
    return np.sqrt(value)

