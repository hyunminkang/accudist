# Quickstart

Import the package using a short alias:

```python
import accudist as ad
```

## Evaluate a distribution

R's `d*`, `p*`, and `q*` naming is preserved:

```python
ad.dnorm(0.0)
ad.pnorm(1.96)
ad.qnorm(0.975)
```

Ask for the upper tail directly instead of subtracting from one. Request the log
result directly instead of logging a rounded probability:

```python
log_upper_tail = ad.ppois(200, 0.1, lower_tail=False, log=True)
```

## Work with arrays

Deterministic functions broadcast over NumPy arrays:

```python
import numpy as np

x = np.array([-2.0, 0.0, 2.0])
probability = ad.pnorm(x)

destination = np.empty_like(x)
ad.dnorm(x, out=destination)
```

Scalar calls return NumPy scalar values; array calls return NumPy arrays.

## Generate random values

Random functions take the draw count first:

```python
ad.set_seed(1234, 5678)
sample = ad.rnorm(1_000, mean=2.0, sd=0.5)
```

Use an `RNG` object when independent streams are clearer than a process-wide
default stream:

```python
rng = ad.RNG(11, 29)
counts = rng.rpois(100, 3.0)
```

These streams do not reproduce R's `set.seed()` output. Read [random
numbers](rng.md) before relying on repeatability.

## Control numerical errors

```python
with ad.errstate(domain="raise"):
    ad.dnorm(0, sd=-1)
```

Continue with [core concepts](user-guide.md) or look up a function in the
[API reference](api-reference.md).
