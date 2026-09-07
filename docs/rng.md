# Random numbers

## The headline caveat

**accudist's `r*` functions do not reproduce R's default `set.seed()` streams.**

R's default uniform generator is Mersenne-Twister. Standalone Rmath, which
accudist vendors, uses a Marsaglia-MultiCarry generator with two 32-bit state
words (`sunif.c`). The *sampling algorithms* (`rpois`, `rbinom`, `rgamma`, ...)
are R's; only the uniform stream underneath differs, which is enough to make
every draw different.

## What *is* reproducible against R

R can be switched to the same generator, and then accudist matches it exactly:

```r
RNGkind("Marsaglia-Multicarry", normal.kind = "Inversion", sample.kind = "Rejection")
set.seed(42)
runif(3); rnorm(3); rpois(3, 4); rgamma(3, 2)
```
```python
import accudist as ad
ad.set_r_seed(42)
ad.runif(3); ad.rnorm(3); ad.rpois(3, 4.0); ad.rgamma(3, 2.0)   # identical to R above
```

`set_r_seed` applies R's own seed scrambling (`RNG_Init` in `src/main/RNG.c`) to
produce the two state words. The test-suite pins these values against R 4.5.2 for
`runif`, `rnorm`, `rpois`, `rbinom`, `rgamma`, `rexp`, `rbeta`, `rt`, the
non-central `rchisq`, `rhyper`, `rwilcox` and `rsignrank`.

!!! note
    R warns that Marsaglia-Multicarry "has poor statistical properties". It is a
    1990s generator with a period around 2^60. For serious simulation work use
    NumPy's `Generator` for the uniforms; accudist's value is in the `d`/`p`/`q`
    functions. The `r*` functions exist for completeness and for reproducing R.

## Streams

`accudist.RNG` holds one `(i1, i2)` state. Every draw installs that state into
the C library under a process-wide lock, runs the whole vectorised draw, and
saves the state back, so streams are independent and thread-safe.

```python
rng = ad.RNG.from_r_seed(7)         # scrambled like R's set.seed(7)
rng = ad.RNG(123456789, 987654321)  # raw state words (avoid small values, see below)
rng.rnorm(5); rng.rpois(5, 2.0); rng.rmultinom(3, size=10, prob=[0.2, 0.3, 0.5])
rng.get_seed(); rng.set_seed(i1, i2); rng.set_r_seed(7)
```

The module-level `ad.rnorm(...)`, `ad.set_seed`, `ad.set_r_seed`, `ad.get_seed`
operate on `ad.default_rng()`, which starts in Rmath's default state `(1234, 5678)`.

!!! warning "Small raw seeds are correlated"
    Marsaglia-MultiCarry mixes small raw state words badly: `RNG(1, 2)` and
    `RNG(3, 4)` produce visibly correlated normals. R avoids this by scrambling
    the user's seed; `RNG.from_r_seed` / `set_r_seed` do the same. Prefer them.

## Signatures

```python
r<dist>(n, <params...>)     # -> float64 array of length n
```

`n` is the draw count. Other parameters recycle to length `n` as in R
(`rnorm(4, mean=[0, 10])` alternates); a parameter longer than `n` is an error.
Where R names the count `nn` because `n` is a distribution parameter, so does
accudist: `rhyper(nn, m, n, k)`, `rwilcox(nn, m, n)`, `rsignrank(nn, n)`. Discrete
draws are returned as `float64`, as R does.

Non-central draws follow R's compositions, consuming the underlying streams in
the same order:

| function | with `ncp` |
|---|---|
| `rchisq(n, df, ncp)` | C `rnchisq` |
| `rbeta(n, s1, s2, ncp)` | `X = rchisq(n, 2*s1, ncp); X / (X + rchisq(n, 2*s2))` |
| `rf(n, df1, df2, ncp)` | `(rchisq(n, df1, ncp)/df1) / (rchisq(n, df2)/df2)` |
| `rt(n, df, ncp)` | `rnorm(n, ncp) / sqrt(rchisq(n, df)/df)` |

## Primitives

`unif_rand(n)`, `norm_rand(n)`, `exp_rand(n)` expose Rmath's generator directly;
`rmultinom(n, size, prob)` returns an `(n, K)` integer array (R returns the
transpose).
