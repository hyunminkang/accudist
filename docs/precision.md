# Precision and the log scale

## Why direct tails matter

A survival probability of 1e-300 is perfectly representable in double precision,
but `1 - cdf` cannot produce it: once the CDF rounds to 1.0 the difference is 0.
On the log scale the situation is worse; `log(1 - cdf)` becomes `-inf` long
before the true value is remarkable. R's `nmath` therefore implements every
`p*` function with a `lower_tail` switch that changes the *algorithm*, and every
`p*`/`q*` with a `log_p` switch, so that

```python
ad.ppois(200, 0.1, lower_tail=False, log=True)   # -1331.4544006213939
```

is computed as a log-sum rather than as `log(1 - 0.99999...)`. accudist exposes
those switches verbatim; it adds no numerics of its own.

## The correctness contract

> For every function on the grids in `tests/data/`, accudist agrees with R 4.5.2
> to **eight significant digits** (relative tolerance 1e-8). NaN matches any NaN,
> infinities match exactly, and values below 1e-300 compare with an absolute floor.

This is deliberately *not* bit-exactness. accudist compiles the very same C
source R compiles, but with a different compiler, on a different libm, sometimes
with a different `long double`. Those produce last-bit differences that are
irrelevant to any statistical use and would make the test-suite platform
dependent. Eight digits is the promise that can be kept everywhere.

The grids (about 21 000 points) are designed rather than sampled: every `p`/`q`
function under all four `lower_tail` x `log` combinations; far tails (`1e-300`,
`1e-100`, `1e-15`, `1 - 1e-10`, log-probabilities down to `-1e5`); support
boundaries, `0`, `+-inf`, `NaN`; domain errors; tiny and huge parameters;
`ncp=None` vs `ncp=0`; both `prob` and `mu`; both `rate` and `scale`.

## Where eight digits is impossible, and why

A few regions of R's own algorithms are not stable to eight digits. They are
listed, with the reason, in `tests/reference_tolerances.py`, and the relaxed
tolerance applies only there:

| region | relaxed to | why |
|---|---|---|
| `qt`, `qchisq`, `qbeta`, `qf` with `ncp` and `1 - p < 1e-8` | 1e-6 | the quantile inverts a `p*` function accurate to ~1e-12; the tail mass being matched has only 4-6 digits |
| `dt` with `ncp` and `|x| >= 50` | 5e-2 | `dnt` is a difference of two `pnt` values; in the far tail they cancel catastrophically and R's answer itself has two digits |
| `ptukey` | 1e-6, or 1e-13 absolute | numerical quadrature; the upper tail is `1 - lower` |
| `qtukey` | 1e-5 | the secant iteration stops at `|x1 - x0| < 1e-4`, as R documents |

Outside these regions the suite has zero tolerance for a ninth-digit surprise: a
mismatch is a bug in the wrapper until proven otherwise.

## Platform notes

- Builds use `-ffp-contract=off` (no fused multiply-add) so that results do not
  depend on whether the CPU has FMA. R's own binaries differ here: R for Apple
  silicon is built with contraction on, which is why a bit-exact comparison with
  R on a Mac fails in a few cancellation-prone spots even though the C source is
  identical.
- nmath's `LDOUBLE` accumulators are compiled as plain `double` on every
  platform (R's own `--disable-long-double` configuration, and what R already
  does on Apple silicon and Windows). With the platform `long double` instead,
  the non-central beta/chi-squared/t/F tails differ between x86_64 (80-bit),
  Linux/aarch64 (128-bit) and the double platforms by far more than the last
  few bits; R itself disagrees with R across those platforms there. Plain
  double makes every accudist wheel return identical numbers, and they match
  the reference values, which were generated with R on Apple silicon.
- R's `cospi`/`sinpi`/`tanpi` on macOS call Apple's `__cospi` family; accudist
  uses nmath's portable implementation everywhere. They agree except for
  arguments around 1e15 where Apple's version is wrong.

## Utilities checked against mpmath

`log1pmx`, `log1pexp`, `log1mexp`, `lgamma1p`, `logspace_add`, `logspace_sub`
have no R-level twin (R exports them only through `Rmath.h`), so they are checked
against 50-digit `mpmath` references to 1e-13 relative.
