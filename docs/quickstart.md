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

## Random draws

```python
ad.set_r_seed(42)                 # like R's set.seed(42) under RNGkind("Marsaglia-Multicarry")
ad.rpois(5, 3.0)
rng = ad.RNG.from_r_seed(7)       # an independent, thread-safe stream
rng.rgamma(1000, shape=2.5, rate=2.0)
```

See [Random numbers](rng.md) for what is and is not reproducible against R.
