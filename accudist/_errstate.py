"""Thread-local policies for warnings reported by R's nmath library."""

from __future__ import annotations

import threading
import warnings
from contextlib import ContextDecorator, contextmanager
from dataclasses import dataclass
from typing import Final

import numpy as np

from . import _ufuncs


class AccudistWarning(RuntimeWarning):
    """Base class for numerical warnings from accudist."""


class AccudistDomainWarning(AccudistWarning):
    pass


class AccudistRangeWarning(AccudistWarning):
    pass


class AccudistConvergenceWarning(AccudistWarning):
    pass


class AccudistPrecisionWarning(AccudistWarning):
    pass


class AccudistUnderflowWarning(AccudistWarning):
    pass


class AccudistDomainError(ValueError):
    pass


class AccudistRangeError(ValueError):
    pass


class AccudistConvergenceError(ValueError):
    pass


class AccudistPrecisionError(ValueError):
    pass


class AccudistUnderflowError(ValueError):
    pass


_VALID: Final = frozenset({"ignore", "warn", "raise"})
_DEFAULTS: Final = {
    "domain": "warn",
    "range": "warn",
    "noconv": "warn",
    "precision": "ignore",
    "underflow": "ignore",
}
_FLAGS: Final = (
    (1 << 0, "domain", "argument out of domain", AccudistDomainWarning, AccudistDomainError),
    (1 << 1, "range", "value out of range", AccudistRangeWarning, AccudistRangeError),
    (1 << 2, "noconv", "convergence failed", AccudistConvergenceWarning, AccudistConvergenceError),
    (1 << 3, "precision", "full precision may not have been achieved", AccudistPrecisionWarning, AccudistPrecisionError),
    (1 << 4, "underflow", "underflow occurred", AccudistUnderflowWarning, AccudistUnderflowError),
)
_ALLOC: Final = 1 << 5
_local = threading.local()


def _policy() -> dict[str, str]:
    policy = getattr(_local, "policy", None)
    if policy is None:
        policy = _DEFAULTS.copy()
        _local.policy = policy
    return policy


class errstate(ContextDecorator):
    """Temporarily set accudist's numerical error policy for this thread."""

    def __init__(
        self,
        *,
        domain: str | None = None,
        range: str | None = None,
        noconv: str | None = None,
        precision: str | None = None,
        underflow: str | None = None,
        all: str | None = None,
    ) -> None:
        requested = {
            "domain": domain,
            "range": range,
            "noconv": noconv,
            "precision": precision,
            "underflow": underflow,
        }
        if all is not None:
            requested = {key: all for key in requested}
        for key, value in requested.items():
            if value is not None and value not in _VALID:
                raise ValueError(
                    f"invalid policy for {key!r}: {value!r}; "
                    "expected 'ignore', 'warn', or 'raise'"
                )
        self._requested = {key: value for key, value in requested.items() if value is not None}
        self._previous: dict[str, str] | None = None

    def __enter__(self) -> errstate:
        current = _policy()
        self._previous = current.copy()
        current.update(self._requested)
        return self

    def __exit__(self, *exc_info: object) -> None:
        if self._previous is not None:
            _local.policy = self._previous


@dataclass
class _Capture:
    function: str

    def __enter__(self) -> _Capture:
        _ufuncs._clear_error()
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def check(self) -> None:
        flags = int(_ufuncs._take_error())
        if flags & _ALLOC:
            raise MemoryError(f"accudist.{self.function}: allocation failed")
        policy = _policy()
        for bit, key, message, warning_type, error_type in _FLAGS:
            if not flags & bit:
                continue
            action = policy[key]
            detail = f"{message} in '{self.function}'"
            if action == "raise":
                raise error_type(detail)
            if action == "warn":
                warnings.warn(detail, warning_type, stacklevel=3)


def capture(function: str) -> _Capture:
    """Capture all nmath flags raised by one generated wrapper call."""

    return _Capture(function)


@contextmanager
def suppress_numpy_warnings():
    """Keep NumPy floating warnings behind accudist's error policy boundary."""

    with np.errstate(all="ignore"):
        yield
