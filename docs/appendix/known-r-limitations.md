---
id: appendix-r-limitations
title: "Appendix: known weak spots in R's own nmath"
status: reference
audience: agents
updated: 2026-08-02
---

# Appendix — known weak spots in R's own nmath

**Reference material, and specifically a list of _candidates_, not approvals.**

Nothing here is a sanctioned deviation. A deviation exists only when a human has
reviewed it into `tests/deviations.toml` — see
[../08-testing.md](../08-testing.md#the-deviation-review-process). Until then,
**accudist matches R**, including where R is wrong.

This page exists so that an agent who finds a discrepancy can tell "known territory,
worth proposing" from "I have a bug in my wrapper". The second is overwhelmingly more
likely: nmath is 25+ years old and exercised by every R user on earth.

---

## Before suspecting R

A mismatch against a golden vector is almost never an R bug. Check, in order:

1. **Argument order.** `ptukey`/`qtukey` swap `nranges` and `nmeans` at the C boundary.
   See the hazards table in [rmath-inventory.md](rmath-inventory.md).
2. **`rate` vs `scale`.** C `dexp`/`pexp`/`qexp` take *scale*; the public parameter is
   *rate*. Same for `gamma`.
3. **`ncp=None` vs `ncp=0.0`.** Different code paths, different answers, both correct.
4. **Compiler flags.** `-ffast-math` or FMA contraction will perturb last bits. Build
   with `-ffp-contract=off`.
5. **The R version.** Golden vectors are pinned to R 4.5.2. A different R may
   legitimately differ.

Only after all five should R itself be suspected.

---

## Candidate regions

These are areas the R community has documented as numerically delicate. They are
starting points for investigation, **not** established errors — each still needs the
evidence bar (a ≥50-digit oracle showing >100 ulp or >3 significant digits of error)
*and* a human review.

| Function | Region | Why it's a candidate |
|---|---|---|
| `qbeta` | very small `shape1` with very large `shape2` (and the mirror image) | Rewritten repeatedly in R's history; the inverse of an already-delicate `pbeta`, so error compounds. |
| `pnbeta` | large `ncp` | Series-based; convergence slows and `ME_PRECISION` fires in normal use. |
| `qnbeta` | far tails | Inherits `pnbeta`'s error and inverts it. |
| `pnchisq` | large `ncp`, far right tail | Documented in the R sources as accuracy-limited; the `MATHLIB_ERROR` in `pnchisq.c` is commented out precisely because it fired too readily. |
| `ptukey` / `qtukey` | large `nranges`, small `df` | Fixed-order quadrature; `qtukey` is a 50-iteration secant search that reports `ME_NOCONV` rather than failing. |
| `pnt` | large `ncp`, `df` small | Series with known slow convergence. |
| `qgamma` | very small `shape` | Newton refinement from an approximate start. |
| `pbinom`/`ppois` far tails | — | **Believed good.** These are the cases accudist exists to serve and they are accurate; listed only so nobody "fixes" them. |

## The DPQ package

Martin Maechler's [DPQ](https://cran.r-project.org/package=DPQ) exists specifically to
study these regions and provides alternative algorithms. It is the **preferred source**
for a replacement algorithm, because it is by an R Core member, published, and already
validated against high-precision references.

`Rmpfr` is the natural companion for generating references where mpmath has no
equivalent — notably `ptukey`, `pwilcox` and `psignrank`, which mpmath does not
implement at all.

## If you believe you have found one

1. Reproduce it in **plain R**, with no accudist involved. If it does not reproduce
   there, it is a wrapper bug — fix the wrapper and stop.
2. Generate a ≥50-digit reference (mpmath, or Rmpfr where mpmath cannot).
3. Quantify the error in ulp and in significant digits. Below the threshold — 100 ulp or
   3 significant digits — stop: record nothing, change nothing.
4. Look for a vetted replacement: R-devel, a published method, or DPQ. If you find none,
   **say so** in the candidate (`replacement = "none — hand-derived"`) rather than
   presenting your own derivation as established. Being unvetted is not disqualifying;
   concealing it is.
5. Write the candidate to `tests/deviations.pending.toml` and **stop**. Leave the
   implementation matching R. Do not change the algorithm, do not regenerate golden
   vectors, do not weaken a test.
6. A human reviews it. If they promote it to `tests/deviations.toml` with `reviewed_by`
   and `reviewed_date`, the deviation takes effect. That decision is not yours.

Filing upstream with R is encouraged and recorded in the entry, but does not block.

Steps 1 and 3 are where nearly all candidates die, and that is the intended outcome.
