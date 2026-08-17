# accudist

Accurate probability distributions for Python, backed by the standalone
mathematical library from R 4.5.2.

`accudist` exposes distribution and special-function algorithms as NumPy-aware
functions. It is designed for work in extreme tails, where computing an upper tail
as `1 - cdf` or taking a logarithm after the fact can lose the result entirely.

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)
# -1331.454...

ad.qnorm(-1000, log=True)
# -44.615...
```

## Install

`accudist` supports CPython 3.10 through 3.14 and requires NumPy.

```console
python -m pip install accudist
```

Start with the [quickstart](quickstart.md), then use the [user guide](user-guide.md)
for R-to-Python conventions or the [API reference](api-reference.md) for every
public distribution, special function, and utility.

## What it provides

- Direct lower-tail, upper-tail, probability, and log-probability algorithms.
- NumPy broadcasting and `out=` support for deterministic functions.
- Density, CDF, quantile, random-generation, and special-function APIs.
- Thread-local numerical error policies.
- A deliberately small `scipy.stats`-style compatibility layer.

## Precision contract

For the same input, finite distribution results are expected to agree with the
official R 4.5.2 binary within 1% relative error. The comparison uses no absolute
tolerance, preserving sensitivity in near-zero tails. NaN results match semantically;
their sign and payload are not portable. Use `lower_tail=False` for the directly
computed upper tail and `log=True` to avoid unnecessary underflow. See
[numerical errors](errors.md) for warning policies.

## Important constraints

The package and its vendored R nmath sources are licensed
**GPL-2.0-or-later**. Evaluate that license before distributing software that
imports it.

Random functions use standalone Rmath's Marsaglia-MultiCarry generator. They use
R's sampling algorithms but do **not** reproduce the stream produced by R's
`set.seed()`. Exact output sequences are not a cross-version compatibility contract.
See [random numbers](rng.md) for reproducible accudist streams.

## Where to go next

- [Installation](installation.md) covers supported Python versions and source builds.
- [Numerical errors](errors.md) explains warnings, exceptions, and `errstate`.
- [Troubleshooting](troubleshooting.md) collects common installation and API issues.
- [Packaging and release](packaging.md) documents the maintainer workflow.
