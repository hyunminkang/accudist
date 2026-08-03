"""Hand-written wrappers for Rmath functions that are not scalar-to-scalar."""

from __future__ import annotations

import numpy as np

from . import _errstate, _ufuncs


def _pairwise(values, operation):
    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        first, second = operation(float(array))
        return np.float64(first), np.float64(second)
    first = np.empty(array.shape, dtype=np.float64)
    second = np.empty(array.shape, dtype=np.float64)
    for index in np.ndindex(array.shape):
        first[index], second[index] = operation(float(array[index]))
    return first, second


def pnorm_both(x, *, log=False):
    """Return R's directly computed lower and upper normal tails."""

    with _errstate.capture("pnorm_both") as captured:
        result = _pairwise(x, lambda value: _ufuncs._pnorm_both_scalar(value, int(log)))
    captured.check()
    return result


def lgammafn_sign(x):
    """Return ``(lgamma(abs(x)), sign(gamma(x)))`` with NumPy broadcasting."""

    with _errstate.capture("lgammafn_sign") as captured:
        value, sign = _pairwise(x, _ufuncs._lgammafn_sign_scalar)
    captured.check()
    if np.ndim(sign) == 0:
        sign = np.intc(sign)
    else:
        sign = np.asarray(sign, dtype=np.intc)
    return value, sign


def rmultinom(n, size, prob):
    """Draw multinomial rows; does not reproduce R's set.seed() stream."""

    from . import _rng

    count = _rng._draw_count(n)
    size = int(size)
    probabilities = np.asarray(prob, dtype=np.float64).reshape(-1)
    if probabilities.size < 1 or np.any(~np.isfinite(probabilities)) or np.any(probabilities < 0):
        raise ValueError("probabilities must be finite and non-negative")
    def draw_rows():
        result = np.empty((count, probabilities.size), dtype=np.intc)
        for row in range(count):
            result[row] = _ufuncs._rmultinom_one(size, probabilities)
        return result

    with _errstate.capture("rmultinom") as captured:
        result = _rng.execute(draw_rows)
    captured.check()
    return result


def logspace_sum(values, axis=-1):
    """Sum exponentials in log space along one array axis."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        raise np.exceptions.AxisError(axis, ndim=0)
    axis = np.core.numeric.normalize_axis_index(axis, array.ndim)
    rows = np.moveaxis(array, axis, -1)
    output = np.empty(rows.shape[:-1], dtype=np.float64)
    for index in np.ndindex(output.shape):
        output[index] = _ufuncs._logspace_sum_1d(rows[index])
    return np.float64(output) if output.ndim == 0 else output
