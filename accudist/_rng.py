"""Standalone Rmath RNG support.

The sampling algorithms are R's, but these streams do not reproduce R's
``set.seed()`` because standalone Rmath uses Marsaglia-MultiCarry rather than
R's default Mersenne-Twister generator.
"""

from __future__ import annotations

import functools
import threading
from contextlib import contextmanager

import numpy as np

from . import _ufuncs


_lock = threading.RLock()
_active = threading.local()


def _draw_count(n) -> int:
    values = np.asarray(n)
    if values.ndim == 0 or values.size == 1:
        value = float(values.reshape(-1)[0])
        if not np.isfinite(value) or value < 0:
            raise ValueError("n must be a finite non-negative number")
        return int(value)
    return int(values.size)


def _recycle(value, size: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size == 0:
        raise ValueError("distribution parameters must not be empty")
    if array.size > size:
        raise ValueError("a distribution parameter is longer than the draw count")
    return np.resize(array, size)


class RNG:
    """An independent deterministic standalone-Rmath random stream."""

    def __init__(self, i1: int = 1234, i2: int = 5678) -> None:
        self.set_seed(i1, i2)

    def set_seed(self, i1: int, i2: int) -> None:
        self._i1 = int(i1) & 0xFFFFFFFF
        self._i2 = int(i2) & 0xFFFFFFFF

    def get_seed(self) -> tuple[int, int]:
        return self._i1, self._i2

    @contextmanager
    def _using(self):
        previous = getattr(_active, "rng", None)
        _active.rng = self
        try:
            yield
        finally:
            _active.rng = previous

    def _draw(self, ufunc, n, *parameters) -> np.ndarray:
        size = _draw_count(n)
        if size == 0:
            return np.empty(0, dtype=np.float64)
        recycled = [_recycle(parameter, size) for parameter in parameters]
        with _lock:
            _ufuncs._set_seed(self._i1, self._i2)
            try:
                result = ufunc(*recycled)
            finally:
                self._i1, self._i2 = map(int, _ufuncs._get_seed())
        return result

    def __getattr__(self, name: str):
        if not name.startswith("r"):
            raise AttributeError(name)
        from . import _api

        function = getattr(_api, name, None)
        if function is None:
            from . import _bespoke

            function = getattr(_bespoke, name, None)
        if function is None or not callable(function):
            raise AttributeError(name)

        @functools.wraps(function)
        def method(*args, **kwargs):
            with self._using():
                return function(*args, **kwargs)

        setattr(self, name, method)
        return method


_default = RNG()


def default_rng() -> RNG:
    return _default


@contextmanager
def locked():
    with _lock:
        yield


def draw(ufunc, n, *parameters) -> np.ndarray:
    rng = getattr(_active, "rng", None) or _default
    return rng._draw(ufunc, n, *parameters)


def set_seed(i1: int, i2: int) -> None:
    _default.set_seed(i1, i2)


def get_seed() -> tuple[int, int]:
    return _default.get_seed()
