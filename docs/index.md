# accudist

`accudist` exposes the probability-distribution algorithms from R 4.5.2 as
NumPy-aware Python functions. Its main purpose is accurate work in extreme tails,
where computing an upper tail as `1 - cdf` or taking a logarithm after the fact can
lose the result entirely.

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

The [user guide](user-guide.md) explains the R-to-Python conventions. The
[generated API reference](api-reference.md) lists every public distribution,
special function, and utility.

## Precision contract

For the same input and supported platform, distribution results are expected to
match the official R 4.5.2 binary at the raw 64-bit floating-point level. Use
`lower_tail=False` for the directly computed upper tail and `log=True` to avoid
unnecessary underflow. See [numerical errors](errors.md) for warning policies.

## Important constraints

The package and its vendored R nmath sources are licensed
**GPL-2.0-or-later**. Evaluate that license before distributing software that
imports it.

Random functions use standalone Rmath's Marsaglia-MultiCarry generator. They use
R's sampling algorithms but do **not** reproduce the stream produced by R's
`set.seed()`. See [random numbers](rng.md) for reproducible accudist streams.
