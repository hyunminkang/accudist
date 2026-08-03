# accudist user guide

`accudist` wraps the probability algorithms shipped in R 4.5.2 as NumPy ufuncs.
Its contract is raw 64-bit agreement with the official R binary on each supported
platform. This matters in upper log tails where subtracting a CDF from one loses all
information.

The package is GPL-2.0-or-later because it includes R's nmath sources. Importing it
into a distributed work can therefore affect that work's licensing; obtain legal
advice when the implication is unclear.

Random functions use standalone Rmath's Marsaglia-MultiCarry stream. They use R's
sampling algorithms but **do not reproduce R's `set.seed()` output**.

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

## scipy compatibility

`accudist.compat` provides the precision-relevant scipy.stats methods for 17 common
distributions, including frozen distributions. It intentionally omits fitting,
moments, entropy, and summary statistics; use scipy for those operations.
