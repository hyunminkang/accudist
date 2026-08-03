---
id: api
title: Public API reference
status: normative
audience: agents
updated: 2026-08-02
---

# 04 — Public API reference

## Naming rules

1. **Distribution functions use R's user-level names**: `ppois`, `dbinom`, `qnorm`,
   `rgamma`. Not the C names, where they differ.
2. **Special functions use Rmath's C names**: `gammafn`, `lgammafn`, `bessel_i`,
   `lchoose`. R calls these `gamma`, `lgamma`, `besselI`, `lchoose` — but `gamma` would
   sit confusingly beside `dgamma`/`pgamma` and shadow `math.gamma`. The rule is
   documented, uniform, and recorded in [ADR-0014](adr/0014-special-function-naming.md).
   Every such function carries `r_equivalent` in `functions.toml` and names the R
   spelling in its docstring.
3. **Parameter names mirror R exactly**, with a PEP 8 trailing underscore only where
   Python forbids the name. In practice that is exactly one: `lambda` → `lambda_`.
4. **`log=` is the only spelling of the log-scale flag**, for d, p, q and r alike.
   R uses `log=` for `d*` and `log.p=` for `p*`/`q*`; accudist unifies on `log=`.
   `log_p=` raises `TypeError`. This is invariant #5.

## Signature shape

```python
d<dist>(x, <params...>,          log=False,                  out=None)
p<dist>(q, <params...>,          lower_tail=True, log=False, out=None)
q<dist>(p, <params...>,          lower_tail=True, log=False, out=None)
r<dist>(n, <params...>,                                            )
```

All parameters after the first may be passed positionally or by keyword. `lower_tail`,
`log` and `out` are keyword-friendly but not keyword-only (positional use matches R).

### Return types

- Scalar input → `numpy.float64` (standard ufunc behaviour). Not a Python `float`.
- Array input → `numpy.ndarray`, fully broadcast.
- `q*` returns **doubles, not integers**, including for discrete distributions —
  exactly as R does. `ad.qpois(0.5, 4.0)` is `4.0`, not `4`.
- `r*` returns a `float64` array of length `n`.

### `lower_tail` is not a convenience

`lower_tail=False` selects a *different algorithm* that computes the upper tail
directly. It is not `1 - cdf`. This is the entire reason accudist exists, and it is why
`ad.ppois(200, 0.1, lower_tail=False, log=True)` returns `-1331.454` where
`scipy.stats.poisson.logsf(200, 0.1)` returns `-inf`.

---

## Argument-order hazards

### `ptukey` / `qtukey` — arguments are genuinely swapped

R presents `ptukey(q, nmeans, df, nranges = 1, ...)` but calls
`.Call(C_ptukey, q, nranges, nmeans, df, ...)`. The C signature is
`ptukey(double q, double rr, double cc, double df, int, int)` where `rr = nranges` and
`cc = nmeans`.

```toml
params = [{ py = "q" }, { py = "nmeans" }, { py = "df" }, { py = "nranges", default = 1.0 }]
[func.call]
c_args = ["nranges", "nmeans", "df"]      # REORDERED — not a typo
```

Getting this wrong returns plausible, wrong numbers rather than an error. There is a
dedicated regression test.

### `dexp` / `pexp` / `qexp` / `rexp` — rate vs scale

The public parameter is `rate` (as in R). The C functions take **scale**. R passes
`1/rate`. `functions.toml` records this as `c_transform = { rate = "1.0 / rate" }`.

### `d/p/q/r hyper` — `n` means two different things

`phyper(q, m, n, k)`: `n` is the number of white balls. But `rhyper(nn, m, n, k)`: the
draw count is `nn`, because `n` is taken. accudist keeps R's names, including `nn`.

### `signrank` — same collision

`rsignrank(nn, n)`. Keep both names.

---

## Parameterisation dispatch

### `ncp=None` — central vs non-central

R decides by `missing(ncp)`, not by value. `pchisq(q, df, ncp=0)` calls `pnchisq`, not
`pchisq`, and the two give slightly different answers. accudist reproduces this with
`ncp=None` as the sentinel:

```python
ad.pchisq(3, df=5)            # C pchisq   — central
ad.pchisq(3, df=5, ncp=0.0)   # C pnchisq  — non-central with ncp 0; differs
ad.pchisq(3, df=5, ncp=1.5)   # C pnchisq
```

Applies to `beta`, `chisq`, `f`, `t` × `d`/`p`/`q`/`r`.

**`r*` with `ncp` is special.** Only `rchisq` has a C implementation (`rnchisq`).
`rbeta`, `rf` and `rt` are *composed in R code*, and accudist must compose them the
same way, in the same order, or the draws differ:

| function | with `ncp` |
|---|---|
| `rchisq` | C `rnchisq(df, ncp)` |
| `rbeta` | `X = rchisq(n, 2*shape1, ncp=ncp); X / (X + rchisq(n, 2*shape2))` |
| `rf` | `(rchisq(n, df1, ncp=ncp)/df1) / (rchisq(n, df2)/df2)` |
| `rt` | `rnorm(n, ncp) / sqrt(rchisq(n, df)/df)` |

`rnbeta` is declared in `Rmath.h` but implemented nowhere — do not call it.

### `prob` xor `mu` — negative binomial

```python
ad.pnbinom(q, size, prob=0.3)   # C pnbinom
ad.pnbinom(q, size, mu=7.0)     # C pnbinom_mu
ad.pnbinom(q, size, 0.3, 7.0)   # TypeError: 'prob' and 'mu' both specified
ad.pnbinom(q, size)             # TypeError: one of 'prob' or 'mu' is required
```

### `rate` xor `scale` — gamma

R warns rather than erroring when `rate * scale` is within `1e-15` of 1, and errors
otherwise. Reproduce both branches:

```python
ad.pgamma(q, shape, rate=2.0)                # scale = 0.5
ad.pgamma(q, shape, scale=0.5)               # same
ad.pgamma(q, shape, rate=2.0, scale=0.5)     # UserWarning (consistent)
ad.pgamma(q, shape, rate=2.0, scale=9.0)     # TypeError  (inconsistent)
```

The C symbol always takes `scale`.

---

## Escape hatches

| Namespace | Contract |
|---|---|
| `accudist` | the supported API; defaults, dispatch, errstate, docstrings |
| `accudist.rmath` | 1:1 with `Rmath.h`; positional, `int` flags, no dispatch, no errstate |
| `accudist._ufuncs` | the raw ufuncs; fastest, no Python overhead; private but documented |

`accudist.rmath` is where `pnchisq`, `dbinom_raw` and `dpois_raw` are reachable. It is
supported for reading but carries no stability guarantee across R version bumps.

---

## Worked examples

```python
import accudist as ad

# The motivating cases
ad.ppois(200, 0.1, lower_tail=False, log=True)          # -1331.4544...
ad.pbinom(900, 1000, 1/6, lower_tail=False, log=True)   # -1312.6880...
ad.qnorm(-1000, log=True)                               # -44.615747...
ad.qbeta(-1000, 0.5, 0.5, log=True)                     # 1.1125e-308

# Broadcasting
import numpy as np
ad.ppois(np.arange(100, 105), 0.1, lower_tail=False, log=True)

# Preallocated output
out = np.empty(5)
ad.ppois(np.arange(100, 105), 0.1, lower_tail=False, log=True, out=out)

# Non-central
ad.pt(2.0, df=10, ncp=1.5)

# Random draws (see 06-rng.md — NOT identical to R's set.seed)
ad.set_seed(1234, 5678)
ad.rpois(5, 0.1)
```

## R → accudist translation

| R | accudist |
|---|---|
| `ppois(q, lambda, lower.tail=FALSE, log.p=TRUE)` | `ad.ppois(q, lambda_, lower_tail=False, log=True)` |
| `dbinom(x, size, prob, log=TRUE)` | `ad.dbinom(x, size, prob, log=True)` |
| `pchisq(q, df, ncp)` | `ad.pchisq(q, df, ncp)` |
| `pgamma(q, shape, rate=2)` | `ad.pgamma(q, shape, rate=2.0)` |
| `ptukey(q, nmeans, df, nranges)` | `ad.ptukey(q, nmeans, df, nranges)` |
| `gamma(x)` | `ad.gammafn(x)` |
| `besselI(x, nu, expon.scaled=TRUE)` | `ad.bessel_i(x, nu, expon_scaled=True)` |
| `psigamma(x, deriv=2)` | `ad.psigamma(x, deriv=2)` |
