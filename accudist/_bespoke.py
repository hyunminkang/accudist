"""Hand-written wrappers for Rmath entry points that are not scalar->scalar."""

from __future__ import annotations

import numpy as np

from . import _ufuncs as _uf
from ._errstate import _check, _clear

__all__ = ["pnorm_both", "lgammafn_sign", "logspace_sum", "free_caches"]


def pnorm_both(x, log=False):
    """Both tails of the standard normal distribution in one pass.

    R equivalent: C ``pnorm_both(x, &cum, &ccum, 2, log_p)`` (no R-level
    function). Returns ``(lower, upper)`` where ``lower == pnorm(x)`` and
    ``upper == pnorm(x, lower_tail=False)``, each on the log scale if ``log``.
    """
    _clear()
    lo, up = _uf.pnorm_both(x, log)
    _check("pnorm_both")
    return lo, up


def lgammafn_sign(x):
    """``log|Gamma(x)|`` together with the sign of ``Gamma(x)``.

    R equivalent: C ``lgammafn_sign(x, &sgn)``. Returns ``(value, sign)``; the
    sign is ``1.0`` or ``-1.0`` as a float so both outputs broadcast identically.
    """
    _clear()
    val, sgn = _uf.lgammafn_sign(x)
    _check("lgammafn_sign")
    return val, sgn


def logspace_sum(logx, axis=-1):
    """``log(sum(exp(logx)))`` along ``axis`` without overflow.

    R equivalent: C ``logspace_sum(const double *, int)`` (R's ``logspace.sum``
    is not exported). Reduces over ``axis`` (default: the last).
    """
    a = np.asarray(logx, dtype=np.float64)
    if a.ndim == 0:
        a = a.reshape(1)
    a = np.moveaxis(a, axis, -1)
    lead = a.shape[:-1]
    flat = np.ascontiguousarray(a.reshape(-1, a.shape[-1]))
    _clear()
    r = _uf.logspace_sum(flat)
    _check("logspace_sum")
    r = r.reshape(lead)
    return r[()] if r.ndim == 0 else r


def free_caches():
    """Release the Wilcoxon rank-sum and signed-rank distribution tables.

    ``dwilcox``/``pwilcox``/``qwilcox`` and the ``signrank`` family cache a table
    whose size grows with ``m``, ``n``. It is freed automatically at interpreter
    exit; call this to reclaim memory earlier.
    """
    from ._core import _cache_lock

    with _cache_lock:
        _uf.free_caches()
