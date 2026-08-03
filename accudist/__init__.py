"""Probability distributions backed by R 4.5.2's standalone nmath library."""

from ._api import *  # noqa: F401,F403
from ._api import __all__ as _function_names
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

__version__ = "0.1.0"
__r_version__ = "4.5.2"

__all__ = [
    *_function_names,
    "errstate",
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

