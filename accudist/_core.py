"""Hand-written helpers shared by the generated wrappers in ``_api.py``."""

from __future__ import annotations

import operator
import threading
import warnings

import numpy as np

from . import _ufuncs as _uf
from ._errstate import AccudistWarning, _check, _clear

# wilcox.c / signrank.c keep a process-wide distribution table in static
# storage; hold this across the whole ufunc call.
_cache_lock = threading.Lock()

# sunif.c holds the generator state in two static ints, and several samplers
# (rbinom, rpois, rhyper) cache derived quantities in statics too.  Re-entrant so
# that composed draws (rbeta/rf/rt with ncp) can nest.
_rng_lock = threading.RLock()

_UINT32_MAX = 0xFFFFFFFF


def r_seed_to_state(seed: int) -> tuple[int, int]:
    """Translate an R ``set.seed(seed)`` into Marsaglia-MultiCarry state words.

    Reproduces ``RNG_Init`` in R's ``src/main/RNG.c``: the seed is cast to an
    unsigned 32-bit integer, scrambled 50 times through the LCG
    ``seed = 69069 * seed + 1``, and the next two LCG outputs become ``(I1, I2)``
    (zero words are replaced by 1). With this state accudist's draws are
    identical to R's after ``RNGkind("Marsaglia-Multicarry", "Inversion",
    "Rejection"); set.seed(seed)``.
    """
    seed = operator.index(seed) & _UINT32_MAX
    for _ in range(50):
        seed = (69069 * seed + 1) & _UINT32_MAX
    words = []
    for _ in range(2):
        seed = (69069 * seed + 1) & _UINT32_MAX
        words.append(seed or 1)
    return words[0], words[1]


def _draw_count(n) -> int:
    try:
        n = operator.index(n)
    except TypeError:
        raise TypeError("n (the number of draws) must be an integer") from None
    if n < 0:
        raise ValueError("n (the number of draws) must be non-negative")
    return n


def _recycle(value, n: int, name: str) -> np.ndarray:
    """Recycle a parameter to length ``n`` the way R does for ``r*`` functions."""
    a = np.asarray(value, dtype=np.float64)
    if a.ndim == 0:
        return np.broadcast_to(a, (n,))
    a = a.ravel()
    if a.size == n:
        return a
    if a.size == 0:
        if n == 0:
            return a
        raise ValueError(f"'{name}' is empty but n = {n}")
    if a.size > n:
        raise ValueError(f"'{name}' has length {a.size}, longer than n = {n}")
    return np.resize(a, n)


def _inv(rate):
    """``1 / rate`` with IEEE semantics (R passes ``1/rate`` as the C scale)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.true_divide(1.0, rate)


def _resolve_rate_scale(rate, scale, fn: str):
    """Reproduce R's ``rate``/``scale`` handling for the gamma family."""
    if scale is None:
        return 1.0 if rate is None else _inv(rate)
    if rate is not None:
        with np.errstate(invalid="ignore"):
            consistent = bool(np.all(np.abs(np.multiply(rate, scale) - 1.0) < 1e-15))
        if not consistent:
            raise TypeError(f"{fn}(): specify 'rate' or 'scale' but not both")
        warnings.warn(f"{fn}(): specify 'rate' or 'scale' but not both", AccudistWarning, stacklevel=3)
    return scale


def _resolve_prob_mu(prob, mu, fn: str) -> bool:
    """Return True when the ``mu`` parametrisation of the negative binomial applies."""
    if mu is None:
        if prob is None:
            raise TypeError(f"{fn}() requires one of 'prob' or 'mu'")
        return False
    if prob is not None:
        raise TypeError(f"{fn}(): 'prob' and 'mu' both specified")
    return True


def _seed_word(value, name: str) -> int:
    v = operator.index(value)
    if not 0 <= v <= _UINT32_MAX:
        raise ValueError(f"{name} must be an unsigned 32-bit integer, got {value!r}")
    return v


class RNGBase:
    """State holder for one Marsaglia-MultiCarry stream (see ``_api.RNG``)."""

    __slots__ = ("_i1", "_i2")

    def __init__(self, i1: int = 1234, i2: int = 5678):
        self._i1 = _seed_word(i1, "i1")
        self._i2 = _seed_word(i2, "i2")

    def set_seed(self, i1: int, i2: int) -> None:
        """Reset the stream to the raw state ``(i1, i2)`` (two unsigned 32-bit words).

        Small raw seeds give poorly mixed, mutually correlated streams (a known
        weakness of Marsaglia-MultiCarry); prefer :meth:`set_r_seed`.
        """
        self._i1 = _seed_word(i1, "i1")
        self._i2 = _seed_word(i2, "i2")

    def set_r_seed(self, seed: int) -> None:
        """Seed exactly as R's ``set.seed(seed)`` does under ``RNGkind("Marsaglia-Multicarry")``.

        After this call, draws reproduce R's provided R was switched to the same
        generator: ``RNGkind("Marsaglia-Multicarry", "Inversion", "Rejection"); set.seed(seed)``.
        R's *default* Mersenne-Twister streams are not reproducible.
        """
        self._i1, self._i2 = r_seed_to_state(seed)

    @classmethod
    def from_r_seed(cls, seed: int):
        """Construct a stream seeded like R's ``set.seed(seed)``; see :meth:`set_r_seed`."""
        return cls(*r_seed_to_state(seed))

    def get_seed(self) -> tuple[int, int]:
        """Return the current state ``(i1, i2)``."""
        return self._i1, self._i2

    def __repr__(self) -> str:
        return f"{type(self).__name__}(i1={self._i1}, i2={self._i2})"

    def _draw(self, name: str, ufunc, args: tuple):
        with _rng_lock:
            _uf.set_seed(self._i1, self._i2)
            _clear()
            try:
                result = ufunc(*args)
            finally:
                self._i1, self._i2 = _uf.get_seed()
        _check(name)
        return result

    def _run(self, name: str, fn, *args):
        """Run a non-ufunc C draw (``unif_rand(n)``, ``rmultinom``) on this stream."""
        with _rng_lock:
            _uf.set_seed(self._i1, self._i2)
            _clear()
            try:
                result = fn(*args)
            finally:
                self._i1, self._i2 = _uf.get_seed()
        return result

    # --- primitives shared by every stream --------------------------------

    def unif_rand(self, n: int) -> np.ndarray:
        """``n`` uniforms on ``[0, 1)`` from Rmath's ``unif_rand()``."""
        r = self._run("unif_rand", _uf.unif_rand, _draw_count(n))
        _check("unif_rand")
        return r

    def norm_rand(self, n: int) -> np.ndarray:
        """``n`` standard normals from Rmath's ``norm_rand()`` (inversion)."""
        r = self._run("norm_rand", _uf.norm_rand, _draw_count(n))
        _check("norm_rand")
        return r

    def exp_rand(self, n: int) -> np.ndarray:
        """``n`` standard exponentials from Rmath's ``exp_rand()``."""
        r = self._run("exp_rand", _uf.exp_rand, _draw_count(n))
        _check("exp_rand")
        return r

    def rmultinom(self, n: int, size: int, prob) -> np.ndarray:
        """Multinomial draws: an ``(n, K)`` integer array with rows summing to ``size``.

        R equivalent: ``rmultinom(n, size, prob)`` (which returns the transpose,
        ``K x n``). ``prob`` is normalised internally; it must sum to 1 within 1e-7.
        """
        n = _draw_count(n)
        size = operator.index(size)
        p = np.ascontiguousarray(prob, dtype=np.float64)
        r = self._run("rmultinom", _uf.rmultinom, size, p, n)
        flags, msg = _uf._take_error()
        if flags & _uf.FLAG_ALLOC and "probability sum" in msg:
            raise ValueError(f"rmultinom(): {msg}")
        if flags:
            from ._errstate import _handle

            _handle("rmultinom", flags, msg)
        return r
