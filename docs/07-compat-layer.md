---
id: compat
title: The scipy compatibility layer
status: normative
audience: agents
updated: 2026-08-02
---

# 07 — The scipy compatibility layer

**Milestone M5.** `accudist.compat` is a *deliberately partial* drop-in for
`scipy.stats`, covering the methods where precision actually matters.

## Contract

```python
from accudist.compat import binom
binom.logsf(900, 1000, 1/6)      # -1312.688   (scipy: -inf)
```

- Frozen and unfrozen forms both work: `binom(1000, 1/6).logsf(900)`.
- Supported methods, and only these:

| | |
|---|---|
| discrete | `pmf` `logpmf` `cdf` `logcdf` `sf` `logsf` `ppf` `isf` `rvs` |
| continuous | `pdf` `logpdf` `cdf` `logcdf` `sf` `logsf` `ppf` `isf` `rvs` |

- **Absent by design**: `fit`, `expect`, `moment`, `stats`, `entropy`, `interval`,
  `median`, `mean`, `var`, `std`, `nnlf`, `support`. These are not precision problems
  and implementing them means owning MLE and moment machinery. Accessing one raises
  `NotImplementedError` with a message pointing at the R-flat API and at scipy.

Do not quietly grow this list. Adding a method requires an ADR.

## Method mapping

| scipy | accudist |
|---|---|
| `.pmf(k, ...)` / `.pdf(x, ...)` | `d*(x, ..., log=False)` |
| `.logpmf` / `.logpdf` | `d*(x, ..., log=True)` |
| `.cdf(x, ...)` | `p*(q, ..., lower_tail=True, log=False)` |
| `.logcdf(x, ...)` | `p*(q, ..., lower_tail=True, log=True)` |
| `.sf(x, ...)` | `p*(q, ..., lower_tail=False, log=False)` |
| `.logsf(x, ...)` | `p*(q, ..., lower_tail=False, log=True)` |
| `.ppf(p, ...)` | `q*(p, ..., lower_tail=True, log=False)` |
| `.isf(p, ...)` | `q*(p, ..., lower_tail=False, log=False)` |
| `.rvs(..., size=n)` | `r*(n, ...)` |

`sf`/`logsf`/`isf` are where the whole value lives: scipy computes `sf` as `1 - cdf`
and underflows; accudist passes `lower_tail=False` into a different algorithm.

## Parameterisation

The shim must accept **scipy's** parameters, not R's, or it is not a drop-in.

| scipy | accudist call |
|---|---|
| `binom(n, p, loc=0)` | `pbinom(k - loc, size=n, prob=p)` |
| `poisson(mu, loc=0)` | `ppois(k - loc, lambda_=mu)` |
| `nbinom(n, p, loc=0)` | `pnbinom(k - loc, size=n, prob=p)` |
| `hypergeom(M, n, N, loc=0)` | `phyper(k - loc, m=n, n=M-n, k=N)` |
| `geom(p, loc=0)` | `pgeom(k - loc - 1, prob=p)` — scipy's geom starts at 1, R's at 0 |
| `norm(loc, scale)` | `pnorm(x, mean=loc, sd=scale)` |
| `gamma(a, loc, scale)` | `pgamma(x - loc, shape=a, scale=scale)` |
| `beta(a, b, loc, scale)` | `pbeta((x-loc)/scale, shape1=a, shape2=b)` |
| `chi2(df, loc, scale)` | `pchisq((x-loc)/scale, df=df)` |
| `t(df, loc, scale)` | `pt((x-loc)/scale, df=df)` |
| `f(dfn, dfd, loc, scale)` | `pf((x-loc)/scale, df1=dfn, df2=dfd)` |
| `expon(loc, scale)` | `pexp(x - loc, rate=1/scale)` |
| `weibull_min(c, loc, scale)` | `pweibull(x - loc, shape=c, scale=scale)` |
| `lognorm(s, loc, scale)` | `plnorm(x - loc, meanlog=log(scale), sdlog=s)` |
| `cauchy(loc, scale)` | `pcauchy(x, location=loc, scale=scale)` |
| `logistic(loc, scale)` | `plogis(x, location=loc, scale=scale)` |
| `uniform(loc, scale)` | `punif(x, min=loc, max=loc+scale)` |

Three traps in that table, each with a dedicated test:

1. **`geom` is off by one.** scipy's geometric counts trials (support starts at 1);
   R's counts failures (support starts at 0).
2. **`hypergeom` reparameterises.** scipy's `(M, n, N)` = (population, successes,
   draws); R's `(m, n, k)` = (white, black, drawn). So `m = n_scipy` and
   `n = M - n_scipy`.
3. **`lognorm`'s `scale` is `exp(meanlog)`**, not a linear scale factor.

Densities need the Jacobian: `pdf` of a scaled variable divides by `scale`, so
`logpdf` **subtracts** `log(scale)`. Get this from the R-flat function and adjust in
Python; never re-derive it in C.

Where no exact mapping exists, raise `NotImplementedError` naming the parameter. Never
approximate.

## Structure

```
accudist/compat/
    __init__.py       exports the distribution instances
    _base.py          _Frozen, _Dist  (shared machinery)
    _discrete.py      binom, poisson, nbinom, geom, hypergeom
    _continuous.py    norm, gamma, beta, chi2, t, f, expon, weibull_min,
                      lognorm, cauchy, logistic, uniform
```

`accudist.compat` may import only the **public** `accudist` namespace — never
`_ufuncs`. If the public API can't express a mapping, the shim must not work around it.

## Testing

Three layers, all in `tests/compat/`:

1. **Agreement.** Where scipy is accurate, `accudist.compat` must agree to `rtol=1e-12`.
   This is what proves the `loc`/`scale`/reparameterisation mapping is right, and it is
   the layer that catches the `geom` and `hypergeom` traps.
2. **Improvement.** On the gap cases, assert accudist is finite and correct where scipy
   is not. Shares fixtures with `tests/test_scipy_gap.py`.
3. **Absence.** Every unimplemented method raises `NotImplementedError` with a message
   naming both the R-flat replacement and scipy — asserted, so the message can't rot.

scipy is a **test-only** dependency. Nothing under `accudist/` imports it.
