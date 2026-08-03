---
id: appendix-scipy-gap
title: "Appendix: measured scipy vs R precision gap"
status: reference
audience: agents
updated: 2026-08-02
---

# Appendix — measured scipy vs R precision gap

**Reference material.** This is the evidence that motivates the project and the seed
corpus for `tests/test_scipy_gap.py`. Do not implement from it — implement from
[../08-testing.md](../08-testing.md).

Measured 2026-08-02 on macOS arm64 with **scipy 1.17.1 / numpy 2.3.5 / Python 3.12.12**
against **R 4.5.2**.

---

## Where scipy fails

| Case | R 4.5.2 | scipy 1.17.1 | Failure |
|---|---|---|---|
| `pbinom(900, 1000, 1/6, lower=F, log=T)` | `-1312.687973` | `-inf` | underflow |
| `ppois(200, 0.1, lower=F, log=T)` | `-1331.454401` | `-inf` | underflow |
| `ppois(1000, 1, lower=F, log=T)` | `-5920.035935` | `-inf` | underflow |
| `pnbinom(1e5, 10, 0.5, lower=F, log=T)` | `-69230.8344` | `-inf` | underflow |
| `pgamma(1e5, 2, lower=F, log=T)` | `-99988.48706` | `-inf` | underflow |
| `pchisq(1e5, 3, lower=F, log=T)` | `-49994.46932` | `-inf` | underflow |
| `pf(1e300, 3, 7, lower=F, log=T)` | `-2413.903706` | `-inf` | underflow |
| `qnorm(-1000, log.p=T)` | `-44.61574773` | `-inf` | no `log_p` input |
| `qgamma(-1000, 2, log.p=T)` | `1.007567258e-217` | `0.0` | no `log_p` input |
| `qbeta(-1000, 0.5, 0.5, log.p=T)` | `1.112536929e-308` | `0.0` | no `log_p` input |
| `qt(-700, 5, log.p=T)` | `-9.923896826e+60` | **`+inf`** | **wrong sign** |
| `ptukey(10, 5, 20, lower=F, log=T)` | `-11.90476371` | *absent* | not implemented |
| `pwilcox(390, 20, 20, lower=F, log=T)` | `-21.07469581` | *absent* | not implemented |
| `psignrank(460, 30, lower=F, log=T)` | `-18.84850527` | *absent* | not implemented |

`qt(-700, 5, log.p=TRUE)` is the worst of these: scipy returns `+inf` where the answer
is large and **negative**. An underflow to `-inf` is at least visibly wrong; a sign
error is not.

## Where scipy is already correct

Equally important — these bound the claim, and each should be an `xfail(strict=False)`
guard so that a future scipy regression is caught rather than assumed.

| Case | R 4.5.2 | scipy 1.17.1 |
|---|---|---|
| `pbinom(500, 1000, 1/6, lower=F, log=T)` | `-298.9632814` | `-298.9632814` ✓ |
| `pgeom(1e4, 0.5, lower=F, log=T)` | `-6932.164953` | `-6932.164953` ✓ |
| `phyper(490, 500, 500, 500, lower=F, log=T)` | `-603.3524591` | `-603.3524591` ✓ |
| `pbeta(1e-300, 0.5, 0.5, log=T)` | `-345.8393467` | `-345.8393467` ✓ |
| `pt(-1e5, 2, log=T)` | `-23.71899811` | `-23.71899811` ✓ |
| `pnorm(-300, log=T)` | `-45006.62273` | `-45006.62273` ✓ |
| `pweibull(1e3, 2, 1, lower=F, log=T)` | `-1000000` | `-1000000` ✓ |
| `pexp(1e4, 1, lower=F, log=T)` | `-10000` | `-10000` ✓ |

## The pattern

Three distinct root causes, worth stating because they shape what accudist must get right:

1. **Discrete upper tails.** scipy computes `sf = 1 - cdf`. Once `cdf` rounds to `1.0`,
   `sf` is `0.0` and `logsf` is `-inf`. R's `lower_tail=FALSE` is a *different
   algorithm* that sums the upper tail directly. Affects `binom`, `pois`, `nbinom`.
2. **Continuous upper tails via the wrong branch.** `pgamma`/`pchisq`/`pf` have the
   same `1 - cdf` problem in the far right tail.
3. **No log-scale input to quantile functions.** scipy's `ppf` takes a probability, so
   the caller must pass `exp(-1000)`, which is already `0.0`. R's `log.p=TRUE` accepts
   the log directly. This is a missing *feature*, not a precision bug, and it cannot be
   worked around by a user.

Continuous `logcdf` in the lower tail is generally fine in scipy. **accudist's value is
concentrated in `lower_tail=False` and in `log=True` inputs to `q*`.**

## Reproducing

```bash
Rscript tools/gap_reference.R          # writes r_out.tsv
python tools/gap_scipy.py              # writes py_out.tsv
python tools/gap_report.py             # renders this table
```

Re-run on every scipy release. When scipy fixes a case, move its row from the first
table to the second rather than deleting it — the history is the argument.
