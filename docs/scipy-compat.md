# SciPy compatibility

`accudist.compat` is a deliberately partial `scipy.stats`-style facade. It provides
tail-accurate distribution evaluation while keeping familiar method names:

- continuous: `pdf`, `logpdf`, `cdf`, `logcdf`, `sf`, `logsf`, `ppf`, `isf`, and
  `rvs`;
- discrete: `pmf`, `logpmf`, `cdf`, `logcdf`, `sf`, `logsf`, `ppf`, `isf`, and
  `rvs`;
- frozen distributions created by calling a distribution object.

```python
from accudist.compat import poisson

poisson.logsf(200, 0.1)
frozen = poisson(0.1)
frozen.logsf(200)
```

Supported distributions are `beta`, `binom`, `cauchy`, `chi2`, `expon`, `f`,
`gamma`, `geom`, `hypergeom`, `logistic`, `lognorm`, `nbinom`, `norm`, `poisson`,
`t`, `uniform`, and `weibull_min`.

The facade intentionally does not implement fitting, moments, entropy, summary
statistics, or arbitrary SciPy `random_state` objects. For the complete SciPy API,
use SciPy directly; use this facade where R's direct log-tail algorithms are the
requirement.
