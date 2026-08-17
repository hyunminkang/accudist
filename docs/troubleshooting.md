# Troubleshooting

## Pip tries to compile the package

First update pip so it can select current wheel tags:

```console
python -m pip install --upgrade pip
python -m pip install accudist
```

If pip still downloads a source archive, confirm that the Python version, operating
system, and CPU architecture have a published wheel. A source installation needs a
C compiler and Python development environment. Include the complete pip output when
reporting an installation problem.

## A tail probability is zero or one

Do not derive an upper tail with `1 - cdf`. Select it directly:

```python
ad.ppois(q, lambda_, lower_tail=False)
```

For very small probabilities, request the natural logarithm directly:

```python
ad.ppois(q, lambda_, lower_tail=False, log=True)
```

## A numerical warning appears

The underlying nmath routine can report domain, range, convergence, precision, or
underflow conditions. See [numerical errors](errors.md) for their default behavior
and for scoped `errstate` policies.

## Random draws differ from R

This is expected. The package uses standalone Rmath's Marsaglia-MultiCarry stream,
not the default Mersenne-Twister stream used by R's `set.seed()`. Exact random
sequences are not a compatibility promise across accudist versions or platforms.
See [random numbers](rng.md).

## A result differs slightly across platforms

Small floating-point differences are expected across compiler and math-library
environments. The compatibility contract is numerical rather than bit-for-bit:
finite distribution results are tested with a relative tolerance, and NaN payload
bits are not portable.

## Report a problem

Open an issue in the [GitHub issue tracker](https://github.com/hyunminkang/accudist/issues)
with the accudist, Python, NumPy, operating-system, and CPU-architecture versions,
plus a minimal example.
