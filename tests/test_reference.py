"""Layer 1: agreement with R 4.5.2 on the designed grids in tests/data/.

The contract is *eight significant digits* (relative tolerance 1e-8), not
bit-exactness: the same nmath algorithm compiled by a different compiler on a
different libm legitimately differs in the last few bits. NaN matches any NaN,
infinities must match exactly, and tiny values compare with an absolute floor
so that 0 and a denormal are considered equal.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

import accudist as ad
from conftest import as_float, load_reference, reference_functions
from reference_tolerances import matches_relaxed, relaxation_for

REL_TOL = 1e-8
ABS_TOL = 1e-300


def values_match(got: float, want: float, rel_tol: float = REL_TOL) -> bool:
    if math.isnan(want):
        return math.isnan(got)
    if math.isinf(want) or math.isinf(got):
        return got == want
    return math.isclose(got, want, rel_tol=rel_tol, abs_tol=ABS_TOL)


@pytest.mark.parametrize("name", reference_functions())
def test_matches_r(name, ignore_nmath_conditions):
    doc = load_reference(name)
    assert doc["meta"]["r_version"] == ad.__r_version__, "reference data and vendored R disagree"
    fn = getattr(ad, name)
    failures = []
    for case in doc["cases"]:
        args = [as_float(a) for a in case["args"]]
        kwargs = {k: as_float(v) for k, v in case["kwargs"].items()}
        want = as_float(case["expected"])
        got = float(fn(*args, **kwargs))
        if values_match(got, want):
            continue
        relaxed = relaxation_for(name, args, kwargs)
        if relaxed is not None and math.isfinite(want) and matches_relaxed(relaxed, got, want, bool(kwargs.get("log", False))):
            continue
        failures.append(f"  {case['r']}\n      R: {want!r}\n      accudist: {got!r}")
    assert not failures, f"{len(failures)}/{len(doc['cases'])} mismatches for {name}:\n" + "\n".join(failures[:25])


@pytest.mark.parametrize("name", reference_functions())
def test_vectorised_matches_scalar(name, ignore_nmath_conditions):
    """Calling once with arrays must equal calling per element (same C loop)."""
    doc = load_reference(name)
    fn = getattr(ad, name)
    # group cases by identical kwargs, so they can be batched along args
    groups: dict[tuple, list] = {}
    for case in doc["cases"]:
        key = tuple(sorted((k, repr(v)) for k, v in case["kwargs"].items()))
        groups.setdefault(key, []).append(case)
    for cases in groups.values():
        if len(cases) < 2:
            continue
        kwargs = {k: as_float(v) for k, v in cases[0]["kwargs"].items()}
        cols = [np.array([as_float(c["args"][i]) for c in cases]) for i in range(len(cases[0]["args"]))]
        batched = fn(*cols, **kwargs)
        for i, c in enumerate(cases):
            single = float(fn(*[as_float(a) for a in c["args"]], **kwargs))
            assert (math.isnan(single) and math.isnan(batched[i])) or batched[i] == single, c["r"]
