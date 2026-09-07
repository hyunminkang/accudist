# Quickstart

```python
import numpy as np
import accudist as ad
```

## The four letters

Every distribution has up to four functions, exactly as in R:

| prefix | meaning | first argument |
|---|---|---|
| `d` | density / mass | `x` |
| `p` | distribution function (CDF) | `q` |
| `q` | quantile function | `p` |
| `r` | random draws | `n` (the number of draws) |

```python
ad.dnorm(1.96)                 # 0.0584...
ad.pnorm(1.96)                 # 0.9750...
ad.qnorm(0.975)                # 1.9599...
ad.rnorm(3)                    # array([...])
```

## Tails and the log scale

`lower_tail=False` selects R's *direct* upper-tail algorithm; it is not `1 - cdf`.
`log=True` returns natural logarithms for `d`, `p` and `q` alike (R spells it
`log.p=` for `p`/`q`; accudist uses `log=` everywhere).

```python
ad.ppois(200, 0.1, lower_tail=False)            # 0.0     underflows in linear space, like R
ad.ppois(200, 0.1, lower_tail=False, log=True)  # -1331.45...  the actual answer
ad.qnorm(-1000, log=True)                        # -44.6157...  quantile of a log-probability
ad.pbinom(900, 1000, 1/6, lower_tail=False, log=True)   # -1312.69
```

## Arrays and broadcasting

Everything is a NumPy ufunc underneath: array arguments broadcast, `out=` writes
into a preallocated array, and scalar inputs return `numpy.float64`.

```python
q = np.arange(100, 105)
ad.ppois(q, 0.1, lower_tail=False, log=True)          # shape (5,)
ad.dnorm(np.zeros((3, 1)), mean=[0.0, 1.0])           # shape (3, 2)

out = np.empty(5)
ad.ppois(q, 0.1, lower_tail=False, log=True, out=out)
```

## Parameterisations, the R way

```python
ad.pgamma(2.0, shape=3, rate=2.0)      # R: pgamma(2, 3, rate = 2)
ad.pgamma(2.0, shape=3, scale=0.5)     # same value
ad.pnbinom(3, size=5, mu=7.0)          # R's mu parameterisation
ad.pchisq(3.0, df=5, ncp=1.5)          # non-central chi-squared
ad.pchisq(3.0, df=5)                   # central algorithm (ncp=None), as in R when ncp is missing
ad.dpois(2, lambda_=3.0)               # lambda is a Python keyword
```

## Special functions

Special functions keep Rmath's C names so `gammafn` sits unambiguously beside
`dgamma`:

```python
ad.gammafn(5.0)            # R: gamma(5)     -> 24
ad.lgammafn(100.0)         # R: lgamma(100)
ad.psigamma(2.0, deriv=1)  # R: psigamma(2, 1) == trigamma(2)
ad.bessel_i(1.0, 0.5, expon_scaled=True)   # R: besselI(1, 0.5, TRUE)
ad.lchoose(1000, 500)      # R: lchoose(1000, 500)
```

## Warnings

Invalid arguments give `NaN` and a warning, like R's "NaNs produced":

```python
ad.qbinom(0.5, -1, 0.5)          # nan, AccudistDomainWarning
with ad.errstate(domain="raise"):
    ad.qbinom(0.5, -1, 0.5)      # raises AccudistDomainError (a ValueError)
with ad.errstate(all="ignore"):
    ad.qbinom(0.5, -1, 0.5)      # nan, silently
```

## Coming from scipy: the compat layer

You can keep scipy's names and parameters. `accudist.compat` provides the same
distribution objects with the same method names, frozen or unfrozen, but every
evaluation goes through R's algorithms. In most code the change is one import:

```python
# from scipy.stats import binom, poisson, nbinom, chi2, gamma, norm
from accudist.compat import binom, poisson, nbinom, chi2, gamma, norm

binom.logsf(900, 1000, 1/6)             # -1312.687973    scipy: -inf
poisson(0.1).logsf(200)                 # -1331.454401    scipy: -inf
nbinom.logsf(1e5, 10, 0.5)              # -69230.834396   scipy: -inf
chi2.logsf(np.array([100, 300, 500]), 10)   # array([-37.45, -133.11, -231.08]); scipy: -inf beyond ~100
```

The methods that matter are `sf`, `logsf` and `isf`. scipy evaluates most
survival functions as `1 - cdf`, which becomes exactly 0 once the CDF rounds to
1, so `logsf` returns `-inf`. accudist calls R's direct upper-tail code
instead. For the log-likelihood of a rare count, a tail p-value below 1e-16, or
an extreme quantile, that is the difference between an answer and no answer.

Where scipy is accurate, both agree to about 1e-12, including `loc` and
`scale`, so switching the import does not change existing results:

```python
from scipy import stats
norm.isf(1e-300)                              # 37.0470962993612 (scipy: same)
gamma.pdf(3.0, 2.5, loc=1, scale=2)           # 0.1383691658068649
stats.gamma.pdf(3.0, 2.5, loc=1, scale=2)     # 0.1383691658068649
d = norm(loc=10, scale=2); d.cdf(12); d.rvs(size=3)
```

Available distributions: `binom`, `poisson`, `nbinom`, `geom`, `hypergeom`,
`norm`, `gamma`, `beta`, `chi2`, `t`, `f`, `expon`, `weibull_min`, `lognorm`,
`cauchy`, `logistic`, `uniform`. Methods: `pmf`/`pdf`, `logpmf`/`logpdf`,
`cdf`, `logcdf`, `sf`, `logsf`, `ppf`, `isf`, `rvs`. Anything else (`fit`,
`mean`, `var`, `entropy`, ...) raises `NotImplementedError` with a pointer to
scipy: the shim is for evaluating distributions precisely, not a scipy
replacement. Three parameterisation traps (`geom` support starting at 1,
`hypergeom`'s `(M, n, N)`, `lognorm`'s `scale = exp(meanlog)`) are handled and
documented in [the compat guide](compat.md).

## Random draws

```python
ad.set_r_seed(42)                 # like R's set.seed(42) under RNGkind("Marsaglia-Multicarry")
ad.rpois(5, 3.0)
rng = ad.RNG.from_r_seed(7)       # an independent, thread-safe stream
rng.rgamma(1000, shape=2.5, rate=2.0)
```

See [Random numbers](rng.md) for what is and is not reproducible against R.
