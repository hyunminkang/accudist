"""Hand-written wrappers for Rmath functions that are not scalar-to-scalar."""

from __future__ import annotations

import numpy as np

from . import _api


def pnorm_both(x, *, log=False):
    """Return R's directly computed lower and upper normal tails."""

    lower = _api.pnorm(x, lower_tail=True, log=log)
    upper = _api.pnorm(x, lower_tail=False, log=log)
    return lower, upper


def lgammafn_sign(x):
    """Return ``(lgamma(abs(x)), sign(gamma(x)))`` with NumPy broadcasting."""

    value = _api.lgammafn(x)
    sign = np.sign(_api.gammafn(x)).astype(np.intc)
    return value, sign


def rmultinom(n, size, prob):
    """Draw multinomial rows; does not reproduce R's set.seed() stream."""

    from . import _rng

    count = _rng._draw_count(n)
    size = int(size)
    probabilities = np.asarray(prob, dtype=np.float64).reshape(-1)
    if probabilities.size < 1 or np.any(~np.isfinite(probabilities)) or np.any(probabilities < 0):
        raise ValueError("probabilities must be finite and non-negative")
    total = float(np.sum(probabilities, dtype=np.longdouble))
    if abs(total - 1.0) > 1e-7:
        raise ValueError("multinomial probabilities must sum to 1")
    result = np.zeros((count, probabilities.size), dtype=np.intc)
    with _rng.locked():
        for row in range(count):
            remaining = size
            remaining_probability = total
            for column in range(probabilities.size - 1):
                probability = probabilities[column]
                if probability != 0.0:
                    conditional = probability / remaining_probability
                    draw = int(_api.rbinom(1, remaining, min(conditional, 1.0))[0])
                    result[row, column] = draw
                    remaining -= draw
                remaining_probability -= probability
            result[row, -1] = remaining
    return result


def logspace_sum(values, axis=-1):
    """Sum exponentials in log space along one array axis."""

    return np.logaddexp.reduce(np.asarray(values, dtype=np.float64), axis=axis)
