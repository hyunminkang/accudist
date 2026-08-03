"""Probability distributions backed by R 4.5.2's standalone nmath library."""

import atexit as _atexit

from ._api import *  # noqa: F401,F403
from ._api import __all__ as _function_names
from ._bespoke import lgammafn_sign, logspace_sum, pnorm_both, rmultinom
from ._errstate import (
    AccudistConvergenceError,
    AccudistConvergenceWarning,
    AccudistDomainError,
    AccudistDomainWarning,
    AccudistPrecisionError,
    AccudistPrecisionWarning,
    AccudistRangeError,
    AccudistRangeWarning,
    AccudistUnderflowError,
    AccudistUnderflowWarning,
    AccudistWarning,
    errstate,
)
from ._rng import RNG, default_rng, get_seed, set_seed
from . import _ufuncs as _raw_ufuncs


def free_caches() -> None:
    """Release the Wilcoxon and sign-rank distribution caches."""

    _raw_ufuncs._free_caches()


_atexit.register(free_caches)

__version__ = "0.1.0"
__r_version__ = "4.5.2"

__all__ = [
    *_function_names,
    "errstate",
    "get_seed",
    "set_seed",
    "RNG",
    "default_rng",
    "free_caches",
    "pnorm_both",
    "lgammafn_sign",
    "rmultinom",
    "logspace_sum",
    "AccudistWarning",
    "AccudistDomainWarning",
    "AccudistRangeWarning",
    "AccudistConvergenceWarning",
    "AccudistPrecisionWarning",
    "AccudistUnderflowWarning",
    "AccudistDomainError",
    "AccudistRangeError",
    "AccudistConvergenceError",
    "AccudistPrecisionError",
    "AccudistUnderflowError",
]
