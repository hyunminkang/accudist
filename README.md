# accudist

[![PyPI](https://img.shields.io/pypi/v/accudist.svg)](https://pypi.org/project/accudist/)
[![Python](https://img.shields.io/pypi/pyversions/accudist.svg)](https://pypi.org/project/accudist/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg)](https://hyunminkang.github.io/accudist/)

`accudist` exposes R 4.5.2's probability-distribution math library as
NumPy-aware functions. It preserves direct tail and log-probability algorithms
that avoid accuracy loss from expressions such as `1 - cdf(x)`.

The package is **GPL-2.0-or-later**, including the vendored R nmath sources, and
its random streams **do not reproduce R's `set.seed()`**. Evaluate both constraints
before adopting it.

## Installation

```console
python -m pip install accudist
```

CPython 3.10 through 3.14 is supported. See the
[installation guide](https://hyunminkang.github.io/accudist/installation/)
for wheel availability and source-build requirements.

## Quick example

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)
# -1331.454...
```

Array inputs broadcast like NumPy ufuncs, and scalar results are NumPy scalars.
The [documentation](https://hyunminkang.github.io/accudist/) includes a
[quickstart](https://hyunminkang.github.io/accudist/quickstart/), the
[user guide](https://hyunminkang.github.io/accudist/user-guide/), and the
[complete API reference](https://hyunminkang.github.io/accudist/api-reference/).

## Licence

This package and its vendored R nmath sources are licensed under
**GPL-2.0-or-later**. Importing `accudist` makes the importing work subject to
the GPL. Evaluate that implication before installing or distributing it.

## Random streams

Random draws use standalone Rmath's deterministic Marsaglia-MultiCarry generator.
They **do not reproduce R's `set.seed()` stream**. The sampling algorithms are R's,
but R's default interpreter generator is Mersenne-Twister. Equal seeds reproduce a
stream within one accudist build; the exact stream is not a compatibility guarantee
across versions, platforms, or alternative generator implementations.

## Performance

Array calls run in generated NumPy ufunc loops. Scalar calls deliberately pay a
Python error-policy wrapper cost; measured results and a reproducible script live in
the [benchmark notes](https://hyunminkang.github.io/accudist/benchmarks/).

## Development

Contributor setup, documentation commands, and release checks are described in the
[packaging and release guide](https://hyunminkang.github.io/accudist/packaging/).
Changes are recorded in the
[changelog](https://github.com/hyunminkang/accudist/blob/HEAD/CHANGELOG.md).
