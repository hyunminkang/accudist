"""accudist: probability distributions with R-grade numerical precision.

Wraps R 4.5.2's ``nmath`` C library as NumPy ufuncs and exposes it with R's own
names, argument order and defaults::

    >>> import accudist as ad
    >>> ad.ppois(200, 0.1, lower_tail=False, log=True)
    -1331.4544006213939

Licensed GPL-2.0-or-later because it links R's GPL sources; importing accudist
makes the importing work subject to the GPL.

Random draws (``r*``) use standalone Rmath's Marsaglia-MultiCarry generator and
do **not** reproduce R's ``set.seed()`` streams.
"""

from __future__ import annotations

import atexit as _atexit

from . import _ufuncs as _uf
from ._api import *  # noqa: F401,F403
from ._api import RNG, __all__ as _api_all, _default_rng
from ._bespoke import free_caches, lgammafn_sign, logspace_sum, pnorm_both
from ._errstate import (
    AccudistConvergenceError,
    AccudistConvergenceWarning,
    AccudistDomainError,
    AccudistDomainWarning,
    AccudistError,
    AccudistPrecisionError,
    AccudistPrecisionWarning,
    AccudistRangeError,
    AccudistRangeWarning,
    AccudistUnderflowError,
    AccudistUnderflowWarning,
    AccudistWarning,
    errstate,
    get_errstate,
)

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("accudist")
except Exception:  # pragma: no cover - source checkout without metadata
    __version__ = "0.0.0+unknown"

__r_version__ = _uf.R_VERSION


def default_rng() -> RNG:
    """Return the module-level :class:`RNG` used by ``accudist.rnorm`` and friends."""
    return _default_rng


def set_seed(i1: int = 1234, i2: int = 5678) -> None:
    """Reset the default stream, mirroring Rmath's C ``set_seed(i1, i2)``.

    This is **not** R's ``set.seed()``: the uniform generator differs, so the
    draws differ from R's even for the same sampling algorithm.
    """
    _default_rng.set_seed(i1, i2)


def set_r_seed(seed: int) -> None:
    """Seed the default stream like R's ``set.seed(seed)`` under ``RNGkind("Marsaglia-Multicarry")``.

    Draws then match R exactly *if* R is switched to the same generator with
    ``RNGkind("Marsaglia-Multicarry", "Inversion", "Rejection")``. They never match
    R's default Mersenne-Twister streams.
    """
    _default_rng.set_r_seed(seed)


def get_seed() -> tuple[int, int]:
    """Return the default stream's state ``(i1, i2)``."""
    return _default_rng.get_seed()


def unif_rand(n: int):
    """``n`` uniforms on ``[0, 1)`` from the default stream (Rmath ``unif_rand``)."""
    return _default_rng.unif_rand(n)


def norm_rand(n: int):
    """``n`` standard normals from the default stream (Rmath ``norm_rand``)."""
    return _default_rng.norm_rand(n)


def exp_rand(n: int):
    """``n`` standard exponentials from the default stream (Rmath ``exp_rand``)."""
    return _default_rng.exp_rand(n)


def rmultinom(n: int, size: int, prob):
    """Multinomial draws from the default stream; see :meth:`RNG.rmultinom`."""
    return _default_rng.rmultinom(n, size, prob)


_atexit.register(_uf.free_caches)

__all__ = list(_api_all) + [
    "__version__",
    "__r_version__",
    "errstate",
    "get_errstate",
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
    "default_rng",
    "set_seed",
    "set_r_seed",
    "get_seed",
    "unif_rand",
    "norm_rand",
    "exp_rand",
    "rmultinom",
    "pnorm_both",
    "lgammafn_sign",
    "logspace_sum",
    "free_caches",
]
