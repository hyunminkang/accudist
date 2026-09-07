"""Warnings, exceptions and the ``errstate`` policy for nmath's error codes.

nmath signals problems through ``ML_WARNING(ME_*)`` (a code) and
``MATHLIB_WARNING(...)`` (a formatted message). Patch 0001 routes both into a
thread-local flag word and message buffer in ``src/accudist_shim.c``. Every
public wrapper clears the word before calling its ufunc and decodes it once
afterwards, here. The word is sticky within one call: it says *whether* any
element hit a condition, not which one.
"""

from __future__ import annotations

import functools
import threading
import warnings

from . import _ufuncs as _uf

__all__ = [
    "errstate",
    "AccudistWarning",
    "AccudistDomainWarning",
    "AccudistRangeWarning",
    "AccudistConvergenceWarning",
    "AccudistPrecisionWarning",
    "AccudistUnderflowWarning",
    "AccudistError",
    "AccudistDomainError",
    "AccudistRangeError",
    "AccudistConvergenceError",
    "AccudistPrecisionError",
    "AccudistUnderflowError",
]


class AccudistWarning(RuntimeWarning):
    """Base class for warnings raised from nmath conditions."""


class AccudistDomainWarning(AccudistWarning):
    """An argument was out of the function's domain; ``NaN`` was returned."""


class AccudistRangeWarning(AccudistWarning):
    """A value was out of range (overflow / loss of accuracy)."""


class AccudistConvergenceWarning(AccudistWarning):
    """An iterative algorithm did not converge."""


class AccudistPrecisionWarning(AccudistWarning):
    """Full precision may not have been achieved."""


class AccudistUnderflowWarning(AccudistWarning):
    """An underflow occurred."""


class AccudistError(ValueError):
    """Base class for the exceptions raised under ``errstate(...='raise')``."""


class AccudistDomainError(AccudistError):
    pass


class AccudistRangeError(AccudistError):
    pass


class AccudistConvergenceError(AccudistError):
    pass


class AccudistPrecisionError(AccudistError):
    pass


class AccudistUnderflowError(AccudistError):
    pass


# category -> (flag bit, warning class, exception class, message template)
_CATEGORIES = {
    "domain": (1, AccudistDomainWarning, AccudistDomainError, "argument out of domain in '{fn}' (NaNs produced)"),
    "range": (2, AccudistRangeWarning, AccudistRangeError, "value out of range in '{fn}'"),
    "noconv": (4, AccudistConvergenceWarning, AccudistConvergenceError, "convergence failed in '{fn}'"),
    "precision": (8, AccudistPrecisionWarning, AccudistPrecisionError, "full precision may not have been achieved in '{fn}'"),
    "underflow": (16, AccudistUnderflowWarning, AccudistUnderflowError, "underflow occurred in '{fn}'"),
    # a MATHLIB_WARNING message from nmath; the text is R's own
    "message": (64, AccudistWarning, AccudistError, "{msg} (in '{fn}')"),
}
_ALLOC = 32
_ACTIONS = ("ignore", "warn", "raise")

# nmath raises PRECISION/UNDERFLOW routinely in correct operation; R itself does
# not surface them, so neither do we by default.
DEFAULTS = {
    "domain": "warn",
    "range": "warn",
    "noconv": "warn",
    "precision": "ignore",
    "underflow": "ignore",
    "message": "warn",
}

_local = threading.local()


def _current() -> dict:
    return getattr(_local, "policy", DEFAULTS)


def get_errstate() -> dict:
    """Return the active error policy as a dict (a copy)."""
    return dict(_current())


class errstate:
    """Set how nmath conditions are reported, as a context manager or decorator.

    Parameters
    ----------
    all : {'ignore', 'warn', 'raise'}, optional
        Policy for every category (applied first).
    domain, range, noconv, precision, underflow, message : {'ignore', 'warn', 'raise'}, optional
        Per-category overrides. ``message`` covers nmath's free-text warnings
        (for example non-convergence notes from ``pnchisq``).

    Allocation failures always raise :class:`MemoryError`; they are not configurable.

    Examples
    --------
    >>> with accudist.errstate(domain='raise'):
    ...     accudist.qbinom(0.5, -1, 0.5)
    Traceback (most recent call last):
    ...
    AccudistDomainError: argument out of domain in 'qbinom' (NaNs produced)
    >>> with accudist.errstate(all='ignore'):
    ...     accudist.qbinom(0.5, -1, 0.5)
    nan
    """

    def __init__(self, *, all: str | None = None, **categories: str):
        policy = dict(_current())
        if all is not None:
            _validate(all)
            policy = {k: all for k in policy}
        for key, action in categories.items():
            if key not in _CATEGORIES:
                raise TypeError(f"unknown errstate category {key!r}; expected one of {sorted(_CATEGORIES)}")
            _validate(action)
            policy[key] = action
        self._policy = policy
        self._stack: list[dict] = []

    def __enter__(self):
        self._stack.append(_current())
        _local.policy = self._policy
        return self

    def __exit__(self, *exc):
        _local.policy = self._stack.pop()
        return False

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper


def _validate(action: str) -> None:
    if action not in _ACTIONS:
        raise ValueError(f"errstate action must be one of {_ACTIONS}, got {action!r}")


_clear = _uf._clear_error


def _check(fn: str) -> None:
    """Decode the thread-local error word set during the last C call."""
    flags, msg = _uf._take_error()
    if not flags:
        return
    _handle(fn, flags, msg)


def _handle(fn: str, flags: int, msg: str) -> None:
    if flags & _ALLOC:
        raise MemoryError(f"accudist.{fn}: {msg or 'allocation failed'}")
    policy = _current()
    for name, (bit, warn_cls, err_cls, template) in _CATEGORIES.items():
        if not flags & bit:
            continue
        action = policy[name]
        if action == "ignore":
            continue
        text = template.format(fn=fn, msg=msg)
        if action == "raise":
            raise err_cls(text)
        warnings.warn(text, warn_cls, stacklevel=4)
