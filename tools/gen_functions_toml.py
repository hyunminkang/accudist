#!/usr/bin/env python3
"""Generate docs/functions.toml, the canonical accudist function inventory.

The tables below were verified mechanically against two sources:

  1. ``Rmath.h`` from the R 4.5.2 standalone math library  -> C symbol + arity
  2. ``args()`` / ``body()`` of R 4.5.2's own R-level closures -> public
     parameter names, defaults, and dispatch rules

Every ``c_args`` list is the *actual* order the C symbol expects, which is NOT
always the public order.  ``ptukey``/``qtukey`` are the notable case: R calls
``.Call(C_ptukey, q, nranges, nmeans, df, ...)`` while presenting
``ptukey(q, nmeans, df, nranges = 1)`` to users.

Run:  python3 tools/gen_functions_toml.py > docs/functions.toml
"""

from __future__ import annotations

R_VERSION = "4.5.2"
SCHEMA_VERSION = 1

# --------------------------------------------------------------------------
# Distribution families.
#
#   params : public parameter list, in public order.
#            (name, default)  -- default None means "required"
#   c_args : names, in C order, of the doubles handed to the C symbol
#   dispatch/alias: see docs/03-codegen-spec.md
# --------------------------------------------------------------------------

# fmt: off
FAMILIES = [
    dict(
        family="norm", r_page="Normal", milestone="M2",
        params=[("mean", "0.0"), ("sd", "1.0")],
        c_args=["mean", "sd"],
    ),
    dict(
        family="unif", r_page="Uniform", milestone="M2",
        params=[("min", "0.0"), ("max", "1.0")],
        c_args=["min", "max"],
    ),
    dict(
        family="gamma", r_page="GammaDist", milestone="M2",
        params=[("shape", None), ("rate", "1.0"), ("scale", None)],
        c_args=["shape", "scale"],
        alias="rate_scale",
    ),
    dict(
        family="beta", r_page="Beta", milestone="M2",
        params=[("shape1", None), ("shape2", None)],
        c_args=["shape1", "shape2"],
        ncp=dict(
            c_prefix="n", c_args=["shape1", "shape2", "ncp"],
            # Rmath.h DECLARES rnbeta but no src/*.c defines it -- linking it
            # fails. R composes the noncentral beta deviate instead.
            r_composed="X = rchisq(n, 2 * shape1, ncp=ncp); X / (X + rchisq(n, 2 * shape2))",
        ),
        ncp_r_missing=True,
    ),
    dict(
        family="lnorm", r_page="Lognormal", milestone="M2",
        params=[("meanlog", "0.0"), ("sdlog", "1.0")],
        c_args=["meanlog", "sdlog"],
    ),
    dict(
        family="chisq", r_page="Chisquare", milestone="M2",
        params=[("df", None)],
        c_args=["df"],
        ncp=dict(c_prefix="n", c_args=["df", "ncp"]),
        ncp_r_missing=True,
        ncp_has_r=True,   # rnchisq exists in C
    ),
    dict(
        family="f", r_page="FDist", milestone="M2",
        params=[("df1", None), ("df2", None)],
        c_args=["df1", "df2"],
        ncp=dict(
            c_prefix="n", c_args=["df1", "df2", "ncp"],
            r_composed="(rchisq(n, df1, ncp=ncp) / df1) / (rchisq(n, df2) / df2)",
        ),
        ncp_r_missing=True,
    ),
    dict(
        family="t", r_page="TDist", milestone="M2",
        params=[("df", None)],
        c_args=["df"],
        ncp=dict(
            c_prefix="n", c_args=["df", "ncp"],
            r_composed="rnorm(n, ncp) / sqrt(rchisq(n, df) / df)",
        ),
        ncp_r_missing=True,
    ),
    dict(
        family="binom", r_page="Binomial", milestone="M2",
        params=[("size", None), ("prob", None)],
        c_args=["size", "prob"],
    ),
    dict(
        family="cauchy", r_page="Cauchy", milestone="M2",
        params=[("location", "0.0"), ("scale", "1.0")],
        c_args=["location", "scale"],
    ),
    dict(
        family="exp", r_page="Exponential", milestone="M2",
        params=[("rate", "1.0")],
        c_args=["rate"],
        # NOTE: C dexp/pexp/qexp take *scale*; R passes 1/rate.
        c_transform={"rate": "1.0 / rate"},
        c_arg_names=["scale"],
    ),
    dict(
        family="geom", r_page="Geometric", milestone="M2",
        params=[("prob", None)],
        c_args=["prob"],
    ),
    dict(
        family="hyper", r_page="Hypergeometric", milestone="M2",
        params=[("m", None), ("n", None), ("k", None)],
        c_args=["m", "n", "k"],
        r_count_name="nn",
    ),
    dict(
        family="nbinom", r_page="NegBinomial", milestone="M2",
        params=[("size", None), ("prob", None), ("mu", None)],
        c_args=["size", "prob"],
        dispatch="prob_or_mu",
        mu=dict(c_suffix="_mu", c_args=["size", "mu"]),
    ),
    dict(
        family="pois", r_page="Poisson", milestone="M2",
        params=[("lambda_", None)],
        c_args=["lambda_"],
    ),
    dict(
        family="weibull", r_page="Weibull", milestone="M2",
        params=[("shape", None), ("scale", "1.0")],
        c_args=["shape", "scale"],
    ),
    dict(
        family="logis", r_page="Logistic", milestone="M2",
        params=[("location", "0.0"), ("scale", "1.0")],
        c_args=["location", "scale"],
    ),
    dict(
        family="wilcox", r_page="Wilcoxon", milestone="M3",
        params=[("m", None), ("n", None)],
        c_args=["m", "n"],
        r_count_name="nn",
        cache="wilcox",
    ),
    dict(
        family="signrank", r_page="SignRank", milestone="M3",
        params=[("n", None)],
        c_args=["n"],
        r_count_name="nn",
        cache="signrank",
    ),
]
# fmt: on

# Tukey is p/q only and reorders its arguments at the C boundary.
TUKEY = dict(
    family="tukey",
    r_page="Tukey",
    milestone="M3",
    params=[("nmeans", None), ("df", None), ("nranges", "1.0")],
    c_args=["nranges", "nmeans", "df"],  # <-- deliberate reorder
    kinds="pq",
)

FIRST_ARG = {"d": "x", "p": "q", "q": "p", "r": "n"}
FLAGS = {"d": ["log"], "p": ["lower_tail", "log"], "q": ["lower_tail", "log"], "r": []}

# --------------------------------------------------------------------------
# Special functions.  These keep their *Rmath C* names (see ADR-0014).
# --------------------------------------------------------------------------
SPECIAL = [
    # (name, c_symbol, params, r_equivalent, milestone, note)
    ("gammafn", "gammafn", [("x", None)], "gamma(x)", "M2", ""),
    ("lgammafn", "lgammafn", [("x", None)], "lgamma(x)", "M2", ""),
    ("digamma", "digamma", [("x", None)], "digamma(x)", "M2", ""),
    ("trigamma", "trigamma", [("x", None)], "trigamma(x)", "M2", ""),
    ("tetragamma", "tetragamma", [("x", None)], "psigamma(x, 2)", "M2", "deprecated in R"),
    ("pentagamma", "pentagamma", [("x", None)], "psigamma(x, 3)", "M2", "deprecated in R"),
    ("psigamma", "psigamma", [("x", None), ("deriv", "0.0")], "psigamma(x, deriv)", "M2", ""),
    ("beta", "beta", [("a", None), ("b", None)], "beta(a, b)", "M2", ""),
    ("lbeta", "lbeta", [("a", None), ("b", None)], "lbeta(a, b)", "M2", ""),
    ("choose", "choose", [("n", None), ("k", None)], "choose(n, k)", "M2", ""),
    ("lchoose", "lchoose", [("n", None), ("k", None)], "lchoose(n, k)", "M2", ""),
    ("bessel_j", "bessel_j", [("x", None), ("nu", None)], "besselJ(x, nu)", "M3", ""),
    ("bessel_y", "bessel_y", [("x", None), ("nu", None)], "besselY(x, nu)", "M3", ""),
]

# besselI/besselK take expon.scaled -> C expo in {1.0, 2.0}
BESSEL_SCALED = [
    ("bessel_i", "bessel_i", "besselI(x, nu, expon.scaled)"),
    ("bessel_k", "bessel_k", "besselK(x, nu, expon.scaled)"),
]

# Numerically-careful helpers with no NumPy equivalent.
UTIL = [
    ("log1pmx", "log1pmx", [("x", None)], "log(1+x) - x, accurate for small x", "M2"),
    ("log1pexp", "log1pexp", [("x", None)], "log(1 + exp(x)) without overflow", "M2"),
    ("lgamma1p", "lgamma1p", [("x", None)], "lgamma(1+x), accurate for small x", "M2"),
    ("logspace_add", "logspace_add", [("logx", None), ("logy", None)], "log(exp(logx) + exp(logy))", "M2"),
    ("logspace_sub", "logspace_sub", [("logx", None), ("logy", None)], "log(exp(logx) - exp(logy))", "M2"),
    ("cospi", "cospi", [("x", None)], "cos(pi*x), exact at half-integers", "M2"),
    ("sinpi", "sinpi", [("x", None)], "sin(pi*x), exact at integers", "M2"),
    ("tanpi", "tanpi", [("x", None)], "tan(pi*x)", "M2"),
    ("fprec", "fprec", [("x", None), ("digits", None)], "round x to `digits` significant digits", "M2"),
    ("fround", "fround", [("x", None), ("digits", None)], "R's round(), banker's rounding", "M2"),
    ("fsign", "fsign", [("x", None), ("y", None)], "|x| * sign(y)", "M2"),
    ("ftrunc", "ftrunc", [("x", None)], "truncate toward zero", "M2"),
    ("sign", "sign", [("x", None)], "-1, 0, or 1", "M2"),
]

# Entry points that are NOT plain scalar->scalar and need bespoke wrappers.
BESPOKE = [
    ("pnorm_both", "pnorm_both", "M3",
     "Writes both lower and upper tail through double* out-params; wrapper "
     "returns a 2-tuple of arrays. Cannot be a plain ufunc."),
    ("lgammafn_sign", "lgammafn_sign", "M3",
     "Returns lgamma via return value and the sign via int* out-param; "
     "wrapper returns a 2-tuple."),
    ("rmultinom", "rmultinom", "M4",
     "Fills an int* vector of length K; wrapper returns an (n, K) int array. "
     "Requires the RNG lock."),
    ("logspace_sum", "logspace_sum", "M4",
     "Takes const double* + length. Expose as a reduction over the last axis, "
     "not a ufunc."),
]

# Exported by Rmath.h but deliberately NOT part of the public API.
EXCLUDED = [
    ("expm1", "duplicate of numpy.expm1"),
    ("log1p", "duplicate of numpy.log1p"),
    ("Rlog1p", "internal alias of log1p"),
    ("hypot", "duplicate of numpy.hypot"),
    ("pythag", "legacy alias of hypot"),
    ("fmax2", "duplicate of numpy.maximum"),
    ("fmin2", "duplicate of numpy.minimum"),
    ("imax2", "trivial integer max"),
    ("imin2", "trivial integer min"),
    ("R_pow", "duplicate of numpy.power"),
    ("R_pow_di", "duplicate of numpy.power"),
    ("R_isnancpp", "internal C++ shim"),
    ("R_finite", "duplicate of numpy.isfinite"),
    ("dpsifn", "internal engine behind psigamma"),
    ("bessel_i_ex", "caller-supplied work array; internal"),
    ("bessel_j_ex", "caller-supplied work array; internal"),
    ("bessel_k_ex", "caller-supplied work array; internal"),
    ("bessel_y_ex", "caller-supplied work array; internal"),
    ("dbinom_raw", "internal helper; reachable via accudist.rmath only"),
    ("dpois_raw", "internal helper; reachable via accudist.rmath only"),
]

# RNG primitives (M4).
RNG_PRIMITIVES = [
    ("unif_rand", "unif_rand", "Marsaglia-MultiCarry uniform on [0,1)"),
    ("norm_rand", "norm_rand", "standard normal, inversion"),
    ("exp_rand", "exp_rand", "standard exponential"),
    ("set_seed", "set_seed", "install global (I1, I2) state"),
    ("get_seed", "get_seed", "read global (I1, I2) state"),
]

out: list[str] = []
w = out.append


def q(s: str) -> str:
    return '"%s"' % s


def arr(xs) -> str:
    return "[" + ", ".join(q(x) for x in xs) + "]"


def emit_params(params, first, kind, fam):
    """Emit the inline param table list."""
    items = ['{ py = "%s" }' % first]
    for name, default in params:
        if default is None:
            items.append('{ py = "%s" }' % name)
        else:
            items.append('{ py = "%s", default = %s }' % (name, default))
    return "params = [\n    " + ",\n    ".join(items) + ",\n]"


w(f"""# accudist canonical function inventory
#
# GENERATED by tools/gen_functions_toml.py -- do not hand-edit in this repo.
# This file is the single source of truth described in docs/03-codegen-spec.md.
# The implementation repo copies it verbatim and drives codegen from it.
#
# Verified against R {R_VERSION}: C symbols and arities from Rmath.h; public
# parameter names, defaults and dispatch rules from R's own closures.

[meta]
schema_version = {SCHEMA_VERSION}
r_version = {q(R_VERSION)}
source_c_header = "vendor/nmath/include/Rmath.h"
notes = "c_args is the order the C symbol expects and is NOT always the public order"
""")

# ---- distribution families ------------------------------------------------
w("\n# =========================================================================")
w("# Distribution functions -- public names follow R's user-level closures.")
w("# =========================================================================")

for fam in FAMILIES:
    family = fam["family"]
    kinds = fam.get("kinds", "dpqr")
    for kind in kinds:
        name = kind + family
        if family == "f" and kind == "d":
            name = "df"  # R really does call it df()
        first = FIRST_ARG[kind]
        if kind == "r" and fam.get("r_count_name"):
            first = fam["r_count_name"]

        params = list(fam["params"])
        c_args = list(fam["c_args"])

        # 'mu' only participates in the nbinom dispatch
        if fam.get("dispatch") == "prob_or_mu":
            pass  # params already include prob and mu

        w("")
        w("[[func]]")
        w(f"name = {q(name)}")
        w(f"kind = {q(kind)}")
        w(f"family = {q(family)}")
        w(f"r_page = {q(fam['r_page'])}")
        w(f"milestone = {q(fam['milestone'])}")
        if fam.get("cache"):
            w(f"cache = {q(fam['cache'])}   # needs *_free() lifecycle, see docs/05-errors.md")
        if fam.get("alias"):
            w(f"alias = {q(fam['alias'])}")
        if fam.get("dispatch"):
            w(f"dispatch = {q(fam['dispatch'])}")
        if fam.get("ncp") and kind in "dpqr":
            has = True
            if kind == "r" and fam["ncp"].get("no_r"):
                has = False
            if has:
                w('dispatch = "ncp"')
        w(emit_params(params, first, kind, fam))
        w(f"flags = {arr(FLAGS[kind])}")
        if fam.get("c_transform"):
            for k, v in fam["c_transform"].items():
                w(f'c_transform = {{ {k} = "{v}" }}')

        w("")
        w("[func.call]")
        w(f"c_symbol = {q(name)}")
        w(f"c_args = {arr(c_args)}")

        if fam.get("ncp"):
            ncp = fam["ncp"]
            if kind == "r" and ncp.get("r_composed"):
                w("")
                w("[func.call_ncp]")
                w(f"composed = {q(ncp['r_composed'])}")
                w('note = "no C symbol; implement in Python exactly as R does"')
            else:
                cname = kind + "n" + family
                w("")
                w("[func.call_ncp]")
                w(f"c_symbol = {q(cname)}")
                w(f"c_args = {arr(ncp['c_args'])}")
        if fam.get("mu"):
            w("")
            w("[func.call_mu]")
            w(f"c_symbol = {q(name + '_mu')}")
            w(f"c_args = {arr(fam['mu']['c_args'])}")

# ---- tukey ----------------------------------------------------------------
w("")
w("# -------------------------------------------------------------------------")
w("# Tukey: the ONLY family where the C argument order differs from the public")
w("# order. R does .Call(C_ptukey, q, nranges, nmeans, df, ...). Getting this")
w("# wrong silently returns plausible-but-wrong numbers -- see docs/08-testing.md.")
w("# -------------------------------------------------------------------------")
for kind in TUKEY["kinds"]:
    name = kind + "tukey"
    w("")
    w("[[func]]")
    w(f"name = {q(name)}")
    w(f"kind = {q(kind)}")
    w('family = "tukey"')
    w(f"r_page = {q(TUKEY['r_page'])}")
    w(f"milestone = {q(TUKEY['milestone'])}")
    w(emit_params(TUKEY["params"], FIRST_ARG[kind], kind, TUKEY))
    w(f"flags = {arr(FLAGS[kind])}")
    w("")
    w("[func.call]")
    w(f"c_symbol = {q(name)}")
    w(f"c_args = {arr(TUKEY['c_args'])}   # REORDERED")

# ---- special functions ----------------------------------------------------
w("")
w("# =========================================================================")
w("# Special functions -- these keep their Rmath C names (ADR-0014).")
w("# =========================================================================")
for name, sym, params, requiv, ms, note in SPECIAL:
    w("")
    w("[[func]]")
    w(f"name = {q(name)}")
    w('kind = "special"')
    w(f"milestone = {q(ms)}")
    w(f"r_equivalent = {q(requiv)}")
    if note:
        w(f"note = {q(note)}")
    items = []
    for pn, pd in params:
        items.append('{ py = "%s" }' % pn if pd is None else '{ py = "%s", default = %s }' % (pn, pd))
    w("params = [\n    " + ",\n    ".join(items) + ",\n]")
    w("flags = []")
    w("")
    w("[func.call]")
    w(f"c_symbol = {q(sym)}")
    w(f"c_args = {arr([p[0] for p in params])}")

for name, sym, requiv in BESSEL_SCALED:
    w("")
    w("[[func]]")
    w(f"name = {q(name)}")
    w('kind = "special"')
    w('milestone = "M3"')
    w(f"r_equivalent = {q(requiv)}")
    w('params = [\n    { py = "x" },\n    { py = "nu" },\n    { py = "expon_scaled", default = false },\n]')
    w("flags = []")
    w('c_transform = { expon_scaled = "2.0 if expon_scaled else 1.0" }')
    w("")
    w("[func.call]")
    w(f"c_symbol = {q(sym)}")
    w('c_args = ["x", "nu", "expon_scaled"]')

# ---- utilities ------------------------------------------------------------
w("")
w("# =========================================================================")
w("# Numerically-careful utilities with no NumPy equivalent.")
w("# =========================================================================")
for name, sym, params, desc, ms in UTIL:
    w("")
    w("[[func]]")
    w(f"name = {q(name)}")
    w('kind = "util"')
    w(f"milestone = {q(ms)}")
    w(f"summary = {q(desc)}")
    items = []
    for pn, pd in params:
        items.append('{ py = "%s" }' % pn if pd is None else '{ py = "%s", default = %s }' % (pn, pd))
    w("params = [\n    " + ",\n    ".join(items) + ",\n]")
    w("flags = []")
    w("")
    w("[func.call]")
    w(f"c_symbol = {q(sym)}")
    w(f"c_args = {arr([p[0] for p in params])}")

# ---- bespoke --------------------------------------------------------------
w("")
w("# =========================================================================")
w("# Not scalar->scalar. These get hand-written wrappers, NOT generated ufuncs.")
w("# =========================================================================")
for name, sym, ms, why in BESPOKE:
    w("")
    w("[[bespoke]]")
    w(f"name = {q(name)}")
    w(f"c_symbol = {q(sym)}")
    w(f"milestone = {q(ms)}")
    w(f"reason = {q(why)}")

# ---- rng ------------------------------------------------------------------
w("")
w("# =========================================================================")
w("# RNG primitives (M4). See docs/06-rng.md -- all require the module lock.")
w("# =========================================================================")
for name, sym, desc in RNG_PRIMITIVES:
    w("")
    w("[[rng_primitive]]")
    w(f"name = {q(name)}")
    w(f"c_symbol = {q(sym)}")
    w(f"summary = {q(desc)}")

# ---- excluded -------------------------------------------------------------
w("")
w("# =========================================================================")
w("# Exported by Rmath.h but deliberately excluded from the public API.")
w("# Agents: do NOT add these. If you think one is needed, write an ADR first.")
w("# =========================================================================")
for name, why in EXCLUDED:
    w("")
    w("[[excluded]]")
    w(f"c_symbol = {q(name)}")
    w(f"reason = {q(why)}")

print("\n".join(out))
