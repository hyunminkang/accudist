# R to accudist

## Naming rules

1. **Distribution functions use R's user-level names**: `ppois`, `dbinom`, `qnorm`,
   `rgamma`, `ptukey`, `pwilcox`, `psignrank`.
2. **Special functions use Rmath's C names**: `gammafn`, `lgammafn`, `digamma`,
   `trigamma`, `psigamma`, `beta`, `lbeta`, `choose`, `lchoose`, `bessel_i/j/k/y`.
   R calls these `gamma`, `lgamma`, `besselI`, ...; the C names avoid shadowing
   `math.gamma` and sitting confusingly next to `dgamma`.
3. **Parameter names mirror R exactly**, with one exception forced by Python:
   `lambda` becomes `lambda_`.
4. **`log=` is the only spelling** of the log-scale flag, for `d`, `p`, `q` alike.
   R uses `log=` for densities and `log.p=` for `p`/`q`. `log_p=` raises `TypeError`.
5. `out=` is keyword-only; `lower_tail` and `log` may be positional, as in R.

## Signature shape

```python
d<dist>(x, <params...>, log=False, *, out=None)
p<dist>(q, <params...>, lower_tail=True, log=False, *, out=None)
q<dist>(p, <params...>, lower_tail=True, log=False, *, out=None)
r<dist>(n, <params...>)
```

Quantiles of discrete distributions are returned as doubles (`ad.qpois(0.5, 4.0)`
is `4.0`), and `r*` return `float64` arrays, exactly as R does.

## Dispatch

### `ncp=None` selects the central algorithm

R decides between the central and non-central code paths by `missing(ncp)`, not by
its value: `pchisq(q, df, ncp = 0)` calls `pnchisq`. accudist reproduces this with
`None` as the sentinel.

```python
ad.pchisq(3, df=5)            # C pchisq   (central)
ad.pchisq(3, df=5, ncp=0.0)   # C pnchisq  (non-central with ncp 0; may differ in the last digits)
ad.pchisq(3, df=5, ncp=1.5)   # C pnchisq
```

Applies to `beta`, `chisq`, `f`, `t` for `d`, `p`, `q`, `r`. Only `rchisq` has a
C non-central sampler; `rbeta`, `rf`, `rt` with `ncp` are composed from `rchisq`
and `rnorm` in the same order R composes them.

### `prob` xor `mu` (negative binomial)

```python
ad.pnbinom(q, size, prob=0.3)   # C pnbinom
ad.pnbinom(q, size, mu=7.0)     # C pnbinom_mu
ad.pnbinom(q, size, 0.3, 7.0)   # TypeError: 'prob' and 'mu' both specified
ad.pnbinom(q, size)             # TypeError: requires one of 'prob' or 'mu'
```

### `rate` xor `scale` (gamma)

R warns if both are given but consistent (`rate * scale` within 1e-15 of 1) and
errors otherwise; accudist does the same (`AccudistWarning` / `TypeError`).

```python
ad.pgamma(q, shape, rate=2.0)              # scale = 0.5
ad.pgamma(q, shape, scale=0.5)             # same
ad.pgamma(q, shape, rate=2.0, scale=0.5)   # warning
ad.pgamma(q, shape, rate=2.0, scale=9.0)   # TypeError
```

### Exponential: `rate`

The C library takes a scale; accudist passes `1 / rate` exactly as R's wrapper does.

## Argument-order hazards handled for you

- **`ptukey` / `qtukey`**: R presents `(q, nmeans, df, nranges)` but the C symbol
  takes `(q, nranges, nmeans, df)`. accudist keeps R's order.
- **`hyper`**: `phyper(q, m, n, k)` where `n` is the number of black balls, so the
  draw count of `rhyper` is called `nn`: `rhyper(nn, m, n, k)`. Same for
  `rwilcox(nn, m, n)` and `rsignrank(nn, n)`.
- **`bessel_i` / `bessel_k`**: `expon_scaled=True` maps to the C `expo = 2`.

## Translation table

| R | accudist |
|---|---|
| `ppois(q, lambda, lower.tail=FALSE, log.p=TRUE)` | `ad.ppois(q, lambda_, lower_tail=False, log=True)` |
| `dbinom(x, size, prob, log=TRUE)` | `ad.dbinom(x, size, prob, log=True)` |
| `qt(p, df, ncp)` | `ad.qt(p, df, ncp=ncp)` |
| `pgamma(q, shape, rate=2)` | `ad.pgamma(q, shape, rate=2.0)` |
| `dexp(x, rate)` | `ad.dexp(x, rate)` |
| `ptukey(q, nmeans, df, nranges)` | `ad.ptukey(q, nmeans, df, nranges)` |
| `pwilcox(q, m, n)` | `ad.pwilcox(q, m, n)` |
| `gamma(x)` / `lgamma(x)` | `ad.gammafn(x)` / `ad.lgammafn(x)` |
| `besselI(x, nu, expon.scaled=TRUE)` | `ad.bessel_i(x, nu, expon_scaled=True)` |
| `psigamma(x, deriv=2)` | `ad.psigamma(x, deriv=2)` |
| `signif(x, d)` / `round(x, d)` | `ad.fprec(x, d)` / `ad.fround(x, d)` |
| `set.seed(s)` under `RNGkind("Marsaglia-Multicarry")` | `ad.set_r_seed(s)` |

## Escape hatches

| namespace | contract |
|---|---|
| `accudist` | the supported API: defaults, dispatch, `errstate`, docstrings |
| `accudist.rmath` | 1:1 with `Rmath.h`: C argument order, `0/1` flags, no dispatch, no error translation; where `pnchisq`, `dbinom_raw`, `dpois_raw` live |
| `accudist._ufuncs` | the raw ufuncs themselves; private, fastest |

```python
from accudist import rmath
rmath.pnchisq(3.0, 5.0, 1.5, 1, 0)      # (x, df, ncp, lower_tail, log_p)
```
