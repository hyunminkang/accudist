---
id: appendix-inventory
title: "Appendix: Rmath.h symbol inventory"
status: reference
audience: agents
updated: 2026-08-02
---

# Appendix — Rmath.h symbol inventory

**Reference material.** The authoritative machine-readable version is
[../functions.toml](../functions.toml); this page is the human-readable rendering.
If the two disagree, `functions.toml` wins and this page is stale.

Verified against R 4.5.2's `Rmath.h`: **153 unique declarations, 100% accounted for**,
with zero references to symbols that are declared but not defined.

## Distribution families

| family | d | p | q | r | public params | R help page | milestone |
|---|---|---|---|---|---|---|---|
| **norm** | `dnorm` | `pnorm` | `qnorm` | `rnorm` | `mean`, `sd` | `Normal` | M2 |
| **unif** | `dunif` | `punif` | `qunif` | `runif` | `min`, `max` | `Uniform` | M2 |
| **gamma** | `dgamma` | `pgamma` | `qgamma` | `rgamma` | `shape`, `rate`, `scale` | `GammaDist` | M2 |
| **beta** | `dbeta` | `pbeta` | `qbeta` | `rbeta` | `shape1`, `shape2` | `Beta` | M2 |
| **lnorm** | `dlnorm` | `plnorm` | `qlnorm` | `rlnorm` | `meanlog`, `sdlog` | `Lognormal` | M2 |
| **chisq** | `dchisq` | `pchisq` | `qchisq` | `rchisq` | `df` | `Chisquare` | M2 |
| **f** | `df` | `pf` | `qf` | `rf` | `df1`, `df2` | `FDist` | M2 |
| **t** | `dt` | `pt` | `qt` | `rt` | `df` | `TDist` | M2 |
| **binom** | `dbinom` | `pbinom` | `qbinom` | `rbinom` | `size`, `prob` | `Binomial` | M2 |
| **cauchy** | `dcauchy` | `pcauchy` | `qcauchy` | `rcauchy` | `location`, `scale` | `Cauchy` | M2 |
| **exp** | `dexp` | `pexp` | `qexp` | `rexp` | `rate` | `Exponential` | M2 |
| **geom** | `dgeom` | `pgeom` | `qgeom` | `rgeom` | `prob` | `Geometric` | M2 |
| **hyper** | `dhyper` | `phyper` | `qhyper` | `rhyper` | `m`, `n`, `k` | `Hypergeometric` | M2 |
| **nbinom** | `dnbinom` | `pnbinom` | `qnbinom` | `rnbinom` | `size`, `prob`, `mu` | `NegBinomial` | M2 |
| **pois** | `dpois` | `ppois` | `qpois` | `rpois` | `lambda_` | `Poisson` | M2 |
| **weibull** | `dweibull` | `pweibull` | `qweibull` | `rweibull` | `shape`, `scale` | `Weibull` | M2 |
| **logis** | `dlogis` | `plogis` | `qlogis` | `rlogis` | `location`, `scale` | `Logistic` | M2 |
| **wilcox** | `dwilcox` | `pwilcox` | `qwilcox` | `rwilcox` | `m`, `n` | `Wilcoxon` | M3 |
| **signrank** | `dsignrank` | `psignrank` | `qsignrank` | `rsignrank` | `n` | `SignRank` | M3 |
| **tukey** | — | `ptukey` | `qtukey` | — | `nmeans`, `df`, `nranges` | `Tukey` | M3 |

## Dispatching functions

Functions whose public call selects among multiple C symbols.

| public | default C symbol | alternate | trigger |
|---|---|---|---|
| `dbeta` | `dbeta` | `dnbeta` | `ncp is not None` |
| `pbeta` | `pbeta` | `pnbeta` | `ncp is not None` |
| `qbeta` | `qbeta` | `qnbeta` | `ncp is not None` |
| `rbeta` | `rbeta` | `*composed in Python*` | `ncp is not None` |
| `dchisq` | `dchisq` | `dnchisq` | `ncp is not None` |
| `pchisq` | `pchisq` | `pnchisq` | `ncp is not None` |
| `qchisq` | `qchisq` | `qnchisq` | `ncp is not None` |
| `rchisq` | `rchisq` | `rnchisq` | `ncp is not None` |
| `df` | `df` | `dnf` | `ncp is not None` |
| `pf` | `pf` | `pnf` | `ncp is not None` |
| `qf` | `qf` | `qnf` | `ncp is not None` |
| `rf` | `rf` | `*composed in Python*` | `ncp is not None` |
| `dt` | `dt` | `dnt` | `ncp is not None` |
| `pt` | `pt` | `pnt` | `ncp is not None` |
| `qt` | `qt` | `qnt` | `ncp is not None` |
| `rt` | `rt` | `*composed in Python*` | `ncp is not None` |
| `dnbinom` | `dnbinom` | `dnbinom_mu` | `mu` given instead of `prob` |
| `pnbinom` | `pnbinom` | `pnbinom_mu` | `mu` given instead of `prob` |
| `qnbinom` | `qnbinom` | `qnbinom_mu` | `mu` given instead of `prob` |
| `rnbinom` | `rnbinom` | `rnbinom_mu` | `mu` given instead of `prob` |

## Argument-order and transform hazards

Only genuine hazards are listed. A C argument list that is a *subset* of the
public list (dispatch or alias resolution) is not a hazard and is omitted.

| public | public order | C order | hazard |
|---|---|---|---|
| `dexp` | `x`, `rate` | `rate` | C receives `rate` as `1.0 / rate` |
| `pexp` | `q`, `rate` | `rate` | C receives `rate` as `1.0 / rate` |
| `qexp` | `p`, `rate` | `rate` | C receives `rate` as `1.0 / rate` |
| `rexp` | `n`, `rate` | `rate` | C receives `rate` as `1.0 / rate` |
| `ptukey` | `q`, `nmeans`, `df`, `nranges` | `nranges`, `nmeans`, `df` | **arguments REORDERED at the C boundary** |
| `qtukey` | `p`, `nmeans`, `df`, `nranges` | `nranges`, `nmeans`, `df` | **arguments REORDERED at the C boundary** |
| `bessel_i` | `x`, `nu`, `expon_scaled` | `x`, `nu`, `expon_scaled` | C receives `expon_scaled` as `2.0 if expon_scaled else 1.0` |
| `bessel_k` | `x`, `nu`, `expon_scaled` | `x`, `nu`, `expon_scaled` | C receives `expon_scaled` as `2.0 if expon_scaled else 1.0` |

8 hazards total.

## Special functions

| accudist | R equivalent | C symbol | milestone |
|---|---|---|---|
| `gammafn` | `gamma(x)` | `gammafn` | M2 |
| `lgammafn` | `lgamma(x)` | `lgammafn` | M2 |
| `digamma` | `digamma(x)` | `digamma` | M2 |
| `trigamma` | `trigamma(x)` | `trigamma` | M2 |
| `tetragamma` | `psigamma(x, 2)` | `tetragamma` | M2 |
| `pentagamma` | `psigamma(x, 3)` | `pentagamma` | M2 |
| `psigamma` | `psigamma(x, deriv)` | `psigamma` | M2 |
| `beta` | `beta(a, b)` | `beta` | M2 |
| `lbeta` | `lbeta(a, b)` | `lbeta` | M2 |
| `choose` | `choose(n, k)` | `choose` | M2 |
| `lchoose` | `lchoose(n, k)` | `lchoose` | M2 |
| `bessel_j` | `besselJ(x, nu)` | `bessel_j` | M3 |
| `bessel_y` | `besselY(x, nu)` | `bessel_y` | M3 |
| `bessel_i` | `besselI(x, nu, expon.scaled)` | `bessel_i` | M3 |
| `bessel_k` | `besselK(x, nu, expon.scaled)` | `bessel_k` | M3 |

## Utilities

Numerically-careful helpers with no NumPy equivalent.

| accudist | purpose | milestone |
|---|---|---|
| `log1pmx` | log(1+x) - x, accurate for small x | M2 |
| `log1pexp` | log(1 + exp(x)) without overflow | M2 |
| `lgamma1p` | lgamma(1+x), accurate for small x | M2 |
| `logspace_add` | log(exp(logx) + exp(logy)) | M2 |
| `logspace_sub` | log(exp(logx) - exp(logy)) | M2 |
| `cospi` | cos(pi*x), exact at half-integers | M2 |
| `sinpi` | sin(pi*x), exact at integers | M2 |
| `tanpi` | tan(pi*x) | M2 |
| `fprec` | round x to `digits` significant digits | M2 |
| `fround` | R's round(), banker's rounding | M2 |
| `fsign` | |x| * sign(y) | M2 |
| `ftrunc` | truncate toward zero | M2 |
| `sign` | -1, 0, or 1 | M2 |

## Bespoke wrappers

Not scalar→scalar; hand-written, never generated.

| symbol | milestone | why |
|---|---|---|
| `pnorm_both` | M3 | Writes both lower and upper tail through double* out-params; wrapper returns a 2-tuple of arrays. Cannot be a plain ufunc. |
| `lgammafn_sign` | M3 | Returns lgamma via return value and the sign via int* out-param; wrapper returns a 2-tuple. |
| `rmultinom` | M4 | Fills an int* vector of length K; wrapper returns an (n, K) int array. Requires the RNG lock. |
| `logspace_sum` | M4 | Takes const double* + length. Expose as a reduction over the last axis, not a ufunc. |

## RNG primitives

| symbol | purpose |
|---|---|
| `unif_rand` | Marsaglia-MultiCarry uniform on [0,1) |
| `norm_rand` | standard normal, inversion |
| `exp_rand` | standard exponential |
| `set_seed` | install global (I1, I2) state |
| `get_seed` | read global (I1, I2) state |

## Deliberately excluded

Exported by `Rmath.h`, absent from the public API. **Do not add these**; each
removal was deliberate. Adding one requires an ADR.

| symbol | reason |
|---|---|
| `expm1` | duplicate of numpy.expm1 |
| `log1p` | duplicate of numpy.log1p |
| `Rlog1p` | internal alias of log1p |
| `hypot` | duplicate of numpy.hypot |
| `pythag` | legacy alias of hypot |
| `fmax2` | duplicate of numpy.maximum |
| `fmin2` | duplicate of numpy.minimum |
| `imax2` | trivial integer max |
| `imin2` | trivial integer min |
| `R_pow` | duplicate of numpy.power |
| `R_pow_di` | duplicate of numpy.power |
| `R_isnancpp` | internal C++ shim |
| `R_finite` | duplicate of numpy.isfinite |
| `dpsifn` | internal engine behind psigamma |
| `bessel_i_ex` | caller-supplied work array; internal |
| `bessel_j_ex` | caller-supplied work array; internal |
| `bessel_k_ex` | caller-supplied work array; internal |
| `bessel_y_ex` | caller-supplied work array; internal |
| `dbinom_raw` | internal helper; reachable via accudist.rmath only |
| `dpois_raw` | internal helper; reachable via accudist.rmath only |

## Symbol traps

| trap | detail |
|---|---|
| `dnorm`/`pnorm`/`qnorm` | macros for `dnorm4`/`pnorm5`/`qnorm5`; everything else is `Rf_<name>` |
| **`rnbeta`** | **declared in `Rmath.h`, defined in no `.c` file — linking it fails.** R composes the non-central beta deviate in R code instead. |
| `log1pexp` | defined as `Rf_log1pexp` in `plogis.c`, not in a file of its own |
| `WILCOX_MAX` | 50; larger `m`/`n` allocate an `O(m·n·max)` table |

