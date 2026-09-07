# The scipy compatibility layer

`accudist.compat` is a *deliberately partial* drop-in for `scipy.stats`. It covers
the evaluation methods where tail precision matters and nothing else.

```python
from accudist.compat import binom, poisson, norm, gamma

binom.logsf(900, 1000, 1/6)          # -1312.688   (scipy: -inf)
binom(1000, 1/6).logsf(900)          # frozen form
poisson(0.1).logsf(200)              # -1331.454
gamma.isf(1e-300, 2.5, scale=2.0)
```

## Supported

| | methods |
|---|---|
| discrete (`binom`, `poisson`, `nbinom`, `geom`, `hypergeom`) | `pmf` `logpmf` `cdf` `logcdf` `sf` `logsf` `ppf` `isf` `rvs` |
| continuous (`norm`, `gamma`, `beta`, `chi2`, `t`, `f`, `expon`, `weibull_min`, `lognorm`, `cauchy`, `logistic`, `uniform`) | `pdf` `logpdf` `cdf` `logcdf` `sf` `logsf` `ppf` `isf` `rvs` |

Distributions take **scipy's** parameters, including `loc` and `scale`, and map
them onto accudist internally. `sf`/`logsf`/`isf` go through R's direct upper-tail
algorithms instead of `1 - cdf`; that is the whole point.

Absent by design: `fit`, `expect`, `moment`, `stats`, `entropy`, `interval`,
`median`, `mean`, `var`, `std`, `nnlf`, `support`. These are not precision
problems. Accessing one raises `NotImplementedError` naming the R-flat
replacement and the scipy original.

## Mapping traps handled

| scipy | accudist | note |
|---|---|---|
| `geom(p)` | `dgeom(k - 1, p)` | scipy counts trials (support from 1); R counts failures (from 0) |
| `hypergeom(M, n, N)` | `dhyper(k, m=n, n=M-n, k=N)` | (population, successes, draws) vs (white, black, drawn) |
| `lognorm(s, loc, scale)` | `dlnorm((x-loc)/scale, 0, s)` | scipy's `scale` is `exp(meanlog)` |
| `expon(loc, scale)` | `dexp((x-loc)/scale, 1)` | |
| `gamma(a, loc, scale)`, `chi2(df, loc, scale)`, `t(df, loc, scale)`, ... | standardised `y = (x-loc)/scale`, density divided by `scale` | |

`rvs(size=...)` draws from `accudist.default_rng()`; it does not accept
`random_state`.

## Tests

- **Agreement**: where scipy is accurate, every method agrees to `rtol=1e-12`
  for every mapped distribution, frozen and unfrozen.
- **Improvement**: on the gap cases accudist is finite and correct where scipy is
  not, and the test also asserts scipy's `-inf` so a scipy fix shows up.
- **Absence**: unimplemented methods raise with the documented message.
