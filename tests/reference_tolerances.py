"""Documented regions where eight-digit agreement with R is not attainable.

Every entry names the functions, the region (a predicate over the public
arguments), the relaxed relative tolerance, and *why* the algorithm itself
cannot do better -- these are limits of R's numerics, not wrapper bugs. Keep
this list short; a new entry needs the same justification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


def _tail_p(args, kw) -> float:
    """The probability being inverted, as a *lower-tail linear* value."""
    p = args[0]
    if kw.get("log", False):
        p = math.exp(p) if p <= 0 else math.nan
    return p


def _near_one(args, kw) -> bool:
    p = _tail_p(args, kw)
    return math.isfinite(p) and 0 < 1 - p < 1e-8


@dataclass(frozen=True)
class Relaxation:
    funcs: frozenset
    when: Callable[[list, dict], bool]
    rel_tol: float
    reason: str
    # absolute tolerance on the *linear-scale probability* (log results are
    # exponentiated first); for functions whose tail is computed as 1 - p
    abs_tol_linear: float = 0.0


RELAXATIONS = [
    Relaxation(
        frozenset({"qt", "qchisq", "qbeta", "qf"}),
        lambda a, kw: kw.get("ncp") is not None and _near_one(a, kw),
        1e-6,
        "non-central quantiles invert the p-function by bisection (qnt) or Newton steps "
        "(qnchisq/qnbeta/qnf) with ~1e-12 accuracy on p; for 1 - p < 1e-8 the tail mass "
        "being matched carries only 4-6 significant digits, so the quantile is not stable "
        "to 8 digits in R either (last-bit differences in p move it).",
    ),
    Relaxation(
        frozenset({"dt"}),
        lambda a, kw: kw.get("ncp") is not None and abs(a[0]) >= 50,
        5e-2,
        "dnt.c evaluates the non-central t density as df/x * (pnt(x*sqrt((df+2)/df), df+2, ncp) "
        "- pnt(x, df, ncp)); in the far tail the two terms cancel catastrophically and R's own "
        "value there has roughly two significant digits.",
    ),
    Relaxation(
        frozenset({"ptukey"}),
        lambda a, kw: True,
        1e-6,
        "ptukey integrates numerically (Gauss-Legendre, eps 1e-14 on the lower tail); the upper "
        "tail is 1 - lower, so it carries an absolute error of ~1e-14 however small it is.",
        abs_tol_linear=1e-13,
    ),
    Relaxation(
        frozenset({"qtukey"}),
        lambda a, kw: True,
        1e-5,
        "qtukey uses a secant iteration that stops once |x1 - x0| < 1e-4; R documents that it "
        "is accurate to about four decimal places.",
    ),
]


def relaxation_for(name: str, args: list, kwargs: dict) -> Relaxation | None:
    for r in RELAXATIONS:
        if name in r.funcs and r.when(args, kwargs):
            return r
    return None


def matches_relaxed(r: Relaxation, got: float, want: float, log: bool) -> bool:
    if math.isclose(got, want, rel_tol=r.rel_tol, abs_tol=1e-300):
        return True
    if r.abs_tol_linear and math.isfinite(got) and math.isfinite(want):
        g, w = (math.exp(got), math.exp(want)) if log else (got, want)
        return abs(g - w) <= r.abs_tol_linear
    return False
