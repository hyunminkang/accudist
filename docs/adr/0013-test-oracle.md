---
id: adr-0013
title: "ADR-0013: Committed golden hex vectors, bit-exact by default"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0013 — Test oracle

## Context

Because accudist compiles R's own C code, results should be bit-identical to R modulo
compiler flags. That permits an unusually strong assertion.

## Decision

`tools/gen_reference.R` sweeps a designed grid under R 4.5.2 and writes values as raw
64-bit hex. Tests assert exact bit equality, with a narrow per-function ulp waiver list
for floating-point-environment differences. Layered on top: invariant tests needing no
oracle, and a scipy-gap regression suite.

## Rejected

| Option | Why not |
|---|---|
| Live R comparison in CI | Every CI job needs an R install (slow, painful on Windows), tests can't run offline, and randomized grids make failures non-reproducible. |
| mpmath as primary ground truth | Contradicts the stated contract, is slow to generate, and mpmath has no `ptukey`/`pwilcox`/`psignrank` at all. Retained as the *second* tier of evidence for the deviation process. |
| Golden vectors with `rtol=1e-13` | A real 100-ulp regression from a bad optimization flag would pass silently. |

## Consequences

- Bit-exactness is a build-flag property too: `-ffp-contract=off`, never `-ffast-math`.
- Hex storage makes a one-ulp diff visible in code review.
- Waivers are for the same algorithm differing in the last bit; deviations
  (ADR-0016) are for deliberately different values. Never conflate them.
