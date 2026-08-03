"""Hand-written wrappers for Rmath functions that are not scalar-to-scalar."""

from __future__ import annotations

import numpy as np

from . import _errstate, _ufuncs


def pnorm_both(x, *, log=False):
    """Return R's directly computed lower and upper normal tails."""

    with np.errstate(all="ignore"), _errstate.capture("pnorm_both") as captured:
        result = _ufuncs._pnorm_both_array(x, int(log))
    captured.check()
    if np.ndim(x) == 0:
        return result[0][()], result[1][()]
    return result


def lgammafn_sign(x):
    """Return ``(lgamma(abs(x)), sign(gamma(x)))`` with NumPy broadcasting."""

    with np.errstate(all="ignore"), _errstate.capture("lgammafn_sign") as captured:
        value, sign = _ufuncs._lgammafn_sign_array(x)
    captured.check()
    if np.ndim(x) == 0:
        return value[()], np.intc(sign[()])
    return value, sign


def rmultinom(n, size, prob):
    """Draw multinomial rows; does not reproduce R's set.seed() stream."""

    from . import _rng

    count = _rng._draw_count(n)
    size = int(size)
    probabilities = np.asarray(prob, dtype=np.float64).reshape(-1)
    if probabilities.size < 1 or np.any(~np.isfinite(probabilities)) or np.any(probabilities < 0):
        raise ValueError("probabilities must be finite and non-negative")
    with np.errstate(all="ignore"), _errstate.capture("rmultinom") as captured:
        result = _rng.execute(lambda: _ufuncs._rmultinom_rows(count, size, probabilities))
    captured.check()
    return result


def logspace_sum(values, axis=-1):
    """Sum exponentials in log space along one array axis."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        raise np.exceptions.AxisError(axis, ndim=0)
    axis = np.core.numeric.normalize_axis_index(axis, array.ndim)
    rows = np.moveaxis(array, axis, -1)
    with np.errstate(all="ignore"), _errstate.capture("logspace_sum") as captured:
        output = _ufuncs._logspace_sum_last(rows)
    captured.check()
    return np.float64(output) if output.ndim == 0 else output
