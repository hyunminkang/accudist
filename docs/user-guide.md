# Core concepts

`accudist` wraps the probability algorithms shipped in R 4.5.2 as NumPy ufuncs.
Finite results agree with the official R binary within 1% relative error, with no
absolute tolerance. NaN sign and payload bits are not part of the contract. This
matters in upper log tails where subtracting a CDF from one loses all information.

The package is GPL-2.0-or-later because it includes R's nmath sources. Importing it
into a distributed work can therefore affect that work's licensing; obtain legal
advice when the implication is unclear.

Random functions use standalone Rmath's Marsaglia-MultiCarry stream. They use R's
sampling algorithms but **do not reproduce R's `set.seed()` output**. Equal seeds are
reproducible within one build, but exact draw sequences are not promised across
versions, platforms, or generator implementations.

## R to accudist

| R | accudist |
|---|---|
| `ppois(q, lambda, lower.tail, log.p)` | `ppois(q, lambda_, lower_tail, log)` |
| `dbinom(x, size, prob, log)` | `dbinom(x, size, prob, log)` |
| `qnorm(p, mean, sd, log.p)` | `qnorm(p, mean, sd, log=...)` |
| `pgamma(q, shape, rate)` | `pgamma(q, shape, rate=...)` |
| `pchisq(q, df, ncp)` | `pchisq(q, df, ncp=...)` |
| `gamma(x)` | `gammafn(x)` |
| `besselI(x, nu, expon.scaled)` | `bessel_i(x, nu, expon_scaled=...)` |

`log=` is the sole spelling for every density, probability, and quantile function.
Use `lower_tail=False` to select R's direct survival-tail algorithm; accudist never
implements that operation as `1 - cdf`.

Scalar inputs return `numpy.float64`; arrays broadcast and support `out=`. Random
functions return float64 arrays and accept an explicit draw count.

## Function families

Distribution function names begin with a letter describing the operation:

| Prefix | Operation | Example |
|---|---|---|
| `d` | density or probability mass | `dnorm(x)` |
| `p` | cumulative probability | `pnorm(q)` |
| `q` | quantile | `qnorm(p)` |
| `r` | random generation | `rnorm(n)` |

Special functions such as `gammafn`, `digamma`, and `bessel_i` use descriptive
names. The [API reference](api-reference.md) is generated from the public API and
is the authoritative function inventory.

## Tail and logarithm arguments

For a probability function, `lower_tail=False` selects the direct upper-tail
algorithm. For a probability or quantile function, `log=True` means the probability
input or output is on the natural-log scale. Density functions use `log=True` to
return the log-density directly.

These flags are numerical operations, not presentation conveniences. Selecting the
direct algorithm can retain information that is already lost in `1 - p` or
`log(p)`.

## Parameters and broadcasting

Arguments follow NumPy broadcasting rules. Parameter names use Python spellings
where R names are not valid or idiomatic Python, such as `lambda_`, `lower_tail`,
and `expon_scaled`. An incompatible shape raises NumPy's normal broadcasting error.

Use `out=` to write a deterministic result into a compatible NumPy array. This can
avoid an allocation in repeated or memory-sensitive calculations.

## scipy compatibility

`accudist.compat` provides the precision-relevant scipy.stats methods for 17 common
distributions, including frozen distributions. It intentionally omits fitting,
moments, entropy, and summary statistics; use scipy for those operations.

See [SciPy compatibility](scipy-compat.md) for the supported methods and
distributions.
