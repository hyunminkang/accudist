# accudist

[![PyPI](https://img.shields.io/pypi/v/accudist.svg)](https://pypi.org/project/accudist/)
[![Python](https://img.shields.io/pypi/pyversions/accudist.svg)](https://pypi.org/project/accudist/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://hyunminkang.github.io/accudist/)

**Probability distributions with R-grade numerical precision, as NumPy ufuncs.**

accudist wraps R 4.5.2's `nmath` C library (the code behind R's `pnorm`, `qbeta`,
`ppois`, ...) and exposes it with R's own names, argument order and defaults.
Its reason to exist is the tails: R computes upper tails and log-probabilities
*directly*, where `scipy.stats` computes `1 - cdf` and underflows.

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)      # -1331.4544006213939   (scipy: -inf)
ad.pbinom(900, 1000, 1/6, lower_tail=False, log=True)  # -1312.687973...     (scipy: -inf)
ad.qnorm(-1000, log=True)                             # -44.61574773...       (scipy: no log_p at all)
ad.pt(2.0, df=10, ncp=1.5)                            # non-central t, R's algorithm
```

| call | R 4.5.2 | accudist | scipy 1.17 |
|---|---|---|---|
| `ppois(200, 0.1, lower=F, log=T)` | -1331.454401 | -1331.454401 | -inf |
| `pgamma(1e5, 2, lower=F, log=T)` | -99988.48706 | -99988.48706 | -inf |
| `pnbinom(1e5, 10, 0.5, lower=F, log=T)` | -69230.83 | -69230.83 | -inf |
| `qbeta(-1000, 0.5, 0.5, log.p=T)` | 1.11e-308 | 1.11e-308 | 0.0 |

## Install

```console
pip install accudist
uv pip install accudist        # or: uv add accudist
```

Binary wheels are published for CPython 3.10 to 3.14 on Linux (x86_64, aarch64),
macOS (Intel, Apple silicon) and Windows (x86_64). Anything else builds from the
sdist automatically, which needs only a C compiler and NumPy headers (no R
installation, no meson, no network beyond PyPI):

```console
pip install accudist --no-binary accudist          # force a source build
pip install git+https://github.com/hyunminkang/accudist    # from the repository
```

See [docs/installation.md](docs/installation.md) for platform notes.

## What you get

- **All 108 scalar functions of `Rmath.h`**: `d`/`p`/`q`/`r` for 21 families
  (normal, uniform, gamma, beta, log-normal, chi-squared, F, t, binomial, Cauchy,
  exponential, geometric, hypergeometric, negative binomial, Poisson, Weibull,
  logistic, Wilcoxon rank-sum and signed-rank, studentized range), the non-central
  beta/chi-squared/F/t via `ncp=`, the gamma/beta/Bessel special functions, and
  R's numerically careful utilities (`log1pmx`, `log1pexp`, `logspace_add`, ...).
- **R semantics, not approximations**: `lower_tail=False` runs a different
  algorithm rather than subtracting; `log=True` works for `d`, `p` and `q`;
  `ncp=None` vs `ncp=0.0`, `prob`/`mu`, `rate`/`scale` dispatch exactly like R.
- **NumPy ufuncs underneath**: broadcasting, `out=`, and array throughput in C.
  Scalar calls return `numpy.float64`.
- **No surprises from C**: nmath's `printf` and `exit(1)` are gone. Conditions
  become Python warnings or exceptions under `accudist.errstate`; a failed
  allocation raises `MemoryError`.
- **Reproducible random streams** via `accudist.RNG`, thread-safe and independent.
- **`accudist.compat`**: a deliberately partial `scipy.stats`-shaped shim
  (`pmf/pdf, cdf, sf, ppf, isf, rvs` and log variants) for drop-in tail fixes.

Full tables: [docs/api-reference.md](docs/api-reference.md).

## R to accudist

| R | accudist |
|---|---|
| `ppois(q, lambda, lower.tail=FALSE, log.p=TRUE)` | `ad.ppois(q, lambda_, lower_tail=False, log=True)` |
| `dbinom(x, size, prob, log=TRUE)` | `ad.dbinom(x, size, prob, log=True)` |
| `pchisq(q, df, ncp)` | `ad.pchisq(q, df, ncp=ncp)` |
| `pgamma(q, shape, rate=2)` | `ad.pgamma(q, shape, rate=2.0)` |
| `pnbinom(q, size, mu=7)` | `ad.pnbinom(q, size, mu=7.0)` |
| `ptukey(q, nmeans, df, nranges)` | `ad.ptukey(q, nmeans, df, nranges)` |
| `gamma(x)`, `lgamma(x)`, `besselI(x, nu, TRUE)` | `ad.gammafn(x)`, `ad.lgammafn(x)`, `ad.bessel_i(x, nu, expon_scaled=True)` |
| `set.seed(42)` (Marsaglia-Multicarry kind) | `ad.set_r_seed(42)` |

Two spellings differ from R on purpose: `lambda_` (a Python keyword) and `log=`
for every function (R uses `log.p=` for `p`/`q`).

## Correctness

Every function is checked against R 4.5.2 on about 21 000 designed grid points
covering all four `lower_tail` x `log` combinations, far tails, support
boundaries, domain errors and extreme parameters. The bar is **agreement to
eight significant digits** (relative tolerance 1e-8), not bit-exactness: the same
algorithm compiled by another compiler on another libm legitimately differs in
the last bits. The handful of regions where R's own algorithm is not stable to
eight digits (e.g. non-central quantiles at `1 - p < 1e-8`, the far tail of the
non-central t density, Tukey quadrature) are listed with reasons in
[tests/reference_tolerances.py](tests/reference_tolerances.py).

## Random numbers

`r*` functions use standalone Rmath's Marsaglia-MultiCarry generator, so they do
**not** reproduce R's default Mersenne-Twister `set.seed()` streams. They *do*
reproduce R exactly if R is switched to the same generator:

```r
RNGkind("Marsaglia-Multicarry", "Inversion", "Rejection"); set.seed(42); rnorm(3)
```
```python
ad.set_r_seed(42); ad.rnorm(3)          # identical values
rng = ad.RNG.from_r_seed(42)            # an independent stream object
```

## Licence

accudist is **GPL-2.0-or-later** because it statically links R's GPL `nmath`
sources. **Importing accudist makes the importing work subject to the GPL.**
Please weigh that before depending on it. R Core Team's copyright headers are
preserved verbatim under `vendor/nmath/`; see [NOTICE](NOTICE).

## Development

```console
git clone https://github.com/hyunminkang/accudist && cd accudist
uv venv && source .venv/bin/activate
uv pip install setuptools numpy pytest hypothesis scipy mpmath
uv pip install --no-build-isolation -e .
pytest -q
```

`functions.toml` drives code generation (`python tools/regen.py`); `vendor/nmath/`
is pristine R source plus the two patches in `vendor/patches/`
(`python tools/sync_rmath.py` re-vendors). Reference data needs R 4.5.2:
`python tools/gen_reference.py`. See [AGENTS.md](AGENTS.md).
