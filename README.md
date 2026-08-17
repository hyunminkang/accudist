# accudist

`accudist` exposes R 4.5.2's probability-distribution math library as NumPy
ufuncs, preserving R's tail algorithms with tight numerical agreement across
supported compiler and math-library environments.

The package is **GPL-2.0-or-later**, including the vendored R nmath sources, and
its random streams **do not reproduce R's `set.seed()`**. Evaluate both constraints
before adopting it. See the [user guide](docs/user-guide.md) for the R-to-Python
mapping, precision model, and distribution API.

```python
import accudist as ad

ad.ppois(200, 0.1, lower_tail=False, log=True)
```

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
[benchmarks/README.md](benchmarks/README.md).
