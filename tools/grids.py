"""Designed evaluation grids for the R reference vectors.

Random sampling is the wrong tool here: the interesting behaviour is at the
edges (far tails, log scale, support boundaries, domain errors, huge and tiny
parameters), so each family gets a hand-picked cross product. Every `p`/`q`
function is evaluated under all four ``lower_tail`` x ``log`` combinations,
because the upper-tail log branch is the reason this package exists.
"""

from __future__ import annotations

import itertools
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
INF = float("inf")
NAN = float("nan")

# --- argument grids ---------------------------------------------------------

REAL_X = [-INF, -1e10, -100.0, -5.0, -1.0, -0.5, -1e-10, 0.0, 1e-10, 0.5, 1.0, 5.0, 38.0, 100.0, 1e10, INF, NAN]
POS_X = [-1.0, 0.0, 1e-300, 1e-10, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 1e3, 1e5, 1e10, INF, NAN]
UNIT_X = [-0.1, 0.0, 1e-300, 1e-10, 0.01, 0.3, 0.5, 0.7, 0.99, 1 - 1e-10, 1.0, 1.1, NAN]
DISC_X = [-1.0, 0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 10.5, 20.0, 50.0, 100.0, 200.0, 900.0, 1e5, INF, NAN]
P = [-0.1, 0.0, 1e-300, 1e-100, 1e-15, 1e-5, 0.001, 0.025, 0.5, 0.975, 0.999, 1 - 1e-10, 1.0, 1.5, NAN]
LOGP = [-1e5, -1000.0, -100.0, -10.0, -1.0, -0.1, -1e-10, 0.0, 0.1, NAN]

# --- parameter sets per family (public parameter names) ---------------------

PARAMS: dict[str, list[dict]] = {
    "norm": [dict(mean=0.0, sd=1.0), dict(mean=-3.5, sd=0.2), dict(mean=1e3, sd=1e-3), dict(mean=0.0, sd=1e10), dict(mean=0.0, sd=-1.0)],
    "unif": [dict(min=0.0, max=1.0), dict(min=-2.0, max=3.0), dict(min=1e-10, max=2e-10), dict(min=1.0, max=0.0)],
    "gamma": [dict(shape=1.0), dict(shape=2.0, rate=2.0), dict(shape=0.5, scale=3.0), dict(shape=1e-3, rate=1.0), dict(shape=100.0, scale=0.1), dict(shape=1e5, rate=1e5), dict(shape=-1.0)],
    "beta": [dict(shape1=0.5, shape2=0.5), dict(shape1=2.0, shape2=5.0), dict(shape1=1e-3, shape2=1e3), dict(shape1=100.0, shape2=100.0), dict(shape1=1.0, shape2=1.0), dict(shape1=-1.0, shape2=2.0)],
    "lnorm": [dict(meanlog=0.0, sdlog=1.0), dict(meanlog=2.0, sdlog=0.1), dict(meanlog=-5.0, sdlog=3.0)],
    "chisq": [dict(df=1.0), dict(df=5.0), dict(df=0.5), dict(df=100.0), dict(df=1e4), dict(df=-1.0)],
    "f": [dict(df1=1.0, df2=1.0), dict(df1=5.0, df2=10.0), dict(df1=100.0, df2=3.0), dict(df1=0.5, df2=1e6), dict(df1=1e4, df2=1e4)],
    "t": [dict(df=1.0), dict(df=5.0), dict(df=0.5), dict(df=30.0), dict(df=1e6), dict(df=INF)],
    "binom": [dict(size=10.0, prob=0.5), dict(size=1000.0, prob=1 / 6), dict(size=1e5, prob=1e-4), dict(size=20.0, prob=0.0), dict(size=20.0, prob=1.0), dict(size=5.0, prob=1.5), dict(size=10.5, prob=0.3)],
    "cauchy": [dict(location=0.0, scale=1.0), dict(location=-2.0, scale=0.01), dict(location=1e5, scale=1e3)],
    "exp": [dict(rate=1.0), dict(rate=0.01), dict(rate=1e4), dict(rate=0.0), dict(rate=-1.0)],
    "geom": [dict(prob=0.5), dict(prob=1e-6), dict(prob=0.999), dict(prob=1.0), dict(prob=0.0)],
    "hyper": [dict(m=10.0, n=7.0, k=8.0), dict(m=1000.0, n=1000.0, k=500.0), dict(m=5.0, n=1e5, k=100.0), dict(m=0.0, n=10.0, k=5.0), dict(m=10.0, n=10.0, k=25.0)],
    "nbinom": [dict(size=3.0, prob=0.4), dict(size=10.0, prob=0.5), dict(size=0.5, prob=1e-3), dict(size=1e4, prob=0.99), dict(size=3.0, mu=7.0), dict(size=1e-3, mu=1e3), dict(size=0.0, prob=0.5)],
    "pois": [dict(lambda_=0.1), dict(lambda_=1.0), dict(lambda_=10.0), dict(lambda_=1e3), dict(lambda_=1e7), dict(lambda_=0.0), dict(lambda_=-1.0)],
    "weibull": [dict(shape=1.0, scale=1.0), dict(shape=0.5, scale=2.0), dict(shape=10.0, scale=0.1), dict(shape=1e-3, scale=1.0)],
    "logis": [dict(location=0.0, scale=1.0), dict(location=3.0, scale=0.1), dict(location=-100.0, scale=1e3)],
    "wilcox": [dict(m=4.0, n=6.0), dict(m=10.0, n=10.0), dict(m=1.0, n=1.0), dict(m=25.0, n=30.0), dict(m=0.0, n=5.0)],
    "signrank": [dict(n=1.0), dict(n=5.0), dict(n=10.0), dict(n=30.0), dict(n=0.0)],
    "tukey": [dict(nmeans=2.0, df=5.0), dict(nmeans=5.0, df=20.0), dict(nmeans=20.0, df=100.0), dict(nmeans=3.0, df=INF), dict(nmeans=5.0, df=20.0, nranges=3.0), dict(nmeans=1.0, df=10.0)],
}

NCP_VALUES = [0.0, 1.5, 25.0]
DISCRETE = {"binom", "geom", "hyper", "nbinom", "pois", "wilcox", "signrank"}
X_GRID = {
    "norm": REAL_X, "cauchy": REAL_X, "logis": REAL_X, "t": REAL_X,
    "unif": [-1.0, 0.0, 1e-10, 0.3, 0.5, 1.0, 1.5, -2.0, 3.0, 2e-10, INF, -INF, NAN],
    "beta": UNIT_X,
    "gamma": POS_X, "lnorm": POS_X, "chisq": POS_X, "f": POS_X, "exp": POS_X, "weibull": POS_X,
    "tukey": [-1.0, 0.0, 0.5, 1.0, 2.0, 3.5, 5.0, 10.0, 50.0, INF, NAN],
}
DISCRETE_X = {
    "wilcox": [-1.0, 0.0, 1.0, 5.0, 10.0, 12.0, 24.0, 50.0, 100.0, 375.0, 749.0, 750.0, 0.5, INF, NAN],
    "signrank": [-1.0, 0.0, 1.0, 5.0, 10.0, 27.0, 28.0, 55.0, 232.0, 465.0, 0.5, INF, NAN],
}


def fam_x(family: str) -> list[float]:
    if family in DISCRETE_X:
        return DISCRETE_X[family]
    if family in DISCRETE:
        return DISC_X
    return X_GRID[family]


def dist_cases(func: dict) -> list[dict]:
    """Cases for one d/p/q function: list of {'args': [...], 'kwargs': {...}}."""
    kind, family = func["kind"], func["family"]
    param_sets = PARAMS[family]
    if func.get("dispatch") == "ncp":
        param_sets = param_sets + [dict(ps, ncp=ncp) for ps in param_sets[:3] for ncp in NCP_VALUES]
    cases = []
    if kind == "d":
        firsts = [(x, {}) for x in fam_x(family)]
        flag_sets = [dict(log=False), dict(log=True)]
    elif kind == "p":
        firsts = [(x, {}) for x in fam_x(family)]
        flag_sets = [dict(lower_tail=lt, log=lg) for lt in (True, False) for lg in (False, True)]
    else:  # q
        firsts = [(p, dict(log=False)) for p in P] + [(lp, dict(log=True)) for lp in LOGP]
        flag_sets = [dict(lower_tail=True), dict(lower_tail=False)]
    for ps in param_sets:
        for first, fixed in firsts:
            for flags in flag_sets:
                kw = dict(ps)
                kw.update(fixed)
                kw.update(flags)
                cases.append({"args": [first], "kwargs": kw})
    return cases


# --- special functions and utilities ------------------------------------------

GAMMA_X = [-INF, -100.5, -5.5, -2.5, -1.0, -0.5, -1e-10, 0.0, 1e-10, 0.5, 1.0, 1.5, 2.0, 10.0, 30.0, 100.0, 170.0, 171.7, 200.0, 1e5, 1e10, INF, NAN]
AB = [1e-10, 0.5, 1.0, 2.0, 10.0, 100.0, 1e5, 0.0, -1.0, INF, NAN]
CHOOSE_N = [0.0, 1.0, 5.0, 10.0, 50.0, 100.0, 1000.0, 0.5, -3.0, 1e6, NAN]
CHOOSE_K = [0.0, 1.0, 2.0, 5.0, 10.0, 49.0, 50.0, 100.0, 500.0, -1.0, NAN]
BESSEL_X = [-1.0, 0.0, 1e-10, 0.1, 1.0, 5.0, 10.0, 100.0, 1000.0, 1e5, NAN]
BESSEL_NU = [0.0, 0.5, 1.0, 2.5, 10.0, 50.0, 100.0, -1.5]
# (1e15 + 0.5 deliberately absent: R on macOS uses Apple's __cospi there and
#  returns 0.38, while nmath's own reduction gives the mathematically correct 0)
TRIG_X = [-2.5, -1.0, -0.5, 0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 1e10, 1e10 + 0.5, INF, NAN]
ROUND_X = [-2.5, -1.2345678, 0.0, 0.5, 1.5, 2.5, 3.14159265358979, 1234.5678, 1e15 + 0.5, 1e300, INF, NAN]
DIGITS = [-2.0, 0.0, 1.0, 2.0, 5.0, 15.0]


def special_cases(func: dict) -> list[dict]:
    name = func["name"]
    if name in ("gammafn", "lgammafn", "digamma", "trigamma", "tetragamma", "pentagamma"):
        return [{"args": [x], "kwargs": {}} for x in GAMMA_X]
    if name == "psigamma":
        return [{"args": [x], "kwargs": {"deriv": d}} for x in GAMMA_X[::2] for d in (0.0, 1.0, 2.0, 3.0, 5.0, 10.0)]
    if name in ("beta", "lbeta"):
        return [{"args": [a, b], "kwargs": {}} for a in AB for b in AB]
    if name in ("choose", "lchoose"):
        return [{"args": [n, k], "kwargs": {}} for n in CHOOSE_N for k in CHOOSE_K]
    if name in ("bessel_j", "bessel_y"):
        return [{"args": [x, nu], "kwargs": {}} for x in BESSEL_X for nu in BESSEL_NU]
    if name in ("bessel_i", "bessel_k"):
        return [{"args": [x, nu], "kwargs": {"expon_scaled": e}} for x in BESSEL_X for nu in BESSEL_NU for e in (False, True)]
    if name in ("cospi", "sinpi", "tanpi"):
        return [{"args": [x], "kwargs": {}} for x in TRIG_X]
    if name in ("fprec", "fround"):
        return [{"args": [x, d], "kwargs": {}} for x in ROUND_X for d in DIGITS]
    if name == "fsign":
        return [{"args": [x, y], "kwargs": {}} for x in (-2.5, 0.0, 3.0, INF, NAN) for y in (-1.0, 0.0, 2.0, -0.0, NAN)]
    if name in ("ftrunc", "sign"):
        return [{"args": [x], "kwargs": {}} for x in ROUND_X + [-0.0, -1e-300]]
    return []  # log1pmx, log1pexp, lgamma1p, logspace_*: checked against mpmath in tests


# --- R rendering --------------------------------------------------------------

R_NAME = {"lambda_": "lambda", "expon_scaled": "expon.scaled", "lower_tail": "lower.tail"}
R_SPECIAL = {
    "gammafn": "gamma({x})", "lgammafn": "lgamma({x})", "digamma": "digamma({x})", "trigamma": "trigamma({x})",
    "tetragamma": "psigamma({x}, 2)", "pentagamma": "psigamma({x}, 3)", "psigamma": "psigamma({x}, {deriv})",
    "beta": "beta({a}, {b})", "lbeta": "lbeta({a}, {b})", "choose": "choose({n}, {k})", "lchoose": "lchoose({n}, {k})",
    "bessel_j": "besselJ({x}, {nu})", "bessel_y": "besselY({x}, {nu})",
    "bessel_i": "besselI({x}, {nu}, expon.scaled={expon_scaled})", "bessel_k": "besselK({x}, {nu}, expon.scaled={expon_scaled})",
    "cospi": "cospi({x})", "sinpi": "sinpi({x})", "tanpi": "tanpi({x})",
    "fprec": "signif({x}, {digits})", "fround": "round({x}, {digits})",
    "fsign": "if ({y} >= 0) abs({x}) else -abs({x})", "ftrunc": "trunc({x})", "sign": "sign({x})",
}


def r_value(v) -> str:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if v != v:
        return "NaN"
    if v == INF:
        return "Inf"
    if v == -INF:
        return "-Inf"
    return repr(float(v))


def r_expr(func: dict, case: dict) -> str:
    name, kind = func["name"], func["kind"]
    if kind in "dpq":
        first = {"d": "x", "p": "q", "q": "p"}[kind]
        parts = [f"{first}={r_value(case['args'][0])}"]
        for k, v in case["kwargs"].items():
            if k == "log":
                parts.append(f"{'log' if kind == 'd' else 'log.p'}={r_value(v)}")
            else:
                parts.append(f"{R_NAME.get(k, k)}={r_value(v)}")
        return f"{name}({', '.join(parts)})"
    names = [p["py"] for p in func["params"]]
    values = dict(zip(names, case["args"]))
    values.update(case["kwargs"])
    return R_SPECIAL[name].format(**{k: r_value(v) for k, v in values.items()})


def all_cases() -> dict[str, tuple[dict, list[dict]]]:
    manifest = tomllib.loads((ROOT / "functions.toml").read_text())
    out = {}
    for f in manifest["func"]:
        if f["kind"] in "dpq":
            cases = dist_cases(f)
        elif f["kind"] in ("special", "util"):
            cases = special_cases(f)
        else:
            continue
        if cases:
            out[f["name"]] = (f, cases)
    return out


if __name__ == "__main__":
    total = 0
    for name, (f, cases) in all_cases().items():
        total += len(cases)
        print(f"{name:14s} {len(cases):5d}   e.g. {r_expr(f, cases[len(cases) // 2])}")
    print(f"total {total}")
