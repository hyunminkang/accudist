---
id: adr-0010
title: "ADR-0010: Include r* on the standalone Marsaglia RNG"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0010 — Including random generation

## Context

The precision problem is entirely in d/p/q. Standalone Rmath's `sunif.c` is
Marsaglia-MultiCarry over two global `unsigned int`s — **not** R's default
Mersenne-Twister. The sampling algorithms are identical to R's; only the uniform
stream differs, which is enough to make every draw differ.

## Decision

Ship `r*` on the standalone RNG, documented prominently as reproducible *within*
accudist but **not identical to R**.

## Rejected

| Option | Why not |
|---|---|
| Defer `r*` entirely to a later phase | Was the recommendation; the user chose to include it now. |
| Port R's `RNG.c` for bit-exact `set.seed` | ~400 more lines of vendored GPL, plus matching R's `rnorm` "Inversion" default and `R_unif_index`, plus thread-local RNG state design. Deferred, not rejected on merit — this remains the upgrade path if R-identical streams are ever wanted. |
| Back `unif_rand` with a NumPy BitGenerator | Not R-reproducible either, and threading a `Generator` through `nogil` loops is genuinely awkward. |

## Consequences

- **The R-incompatibility caveat must appear in every `r*` docstring, the module
  docstring, and the README feature list — not a footnote.** A user assuming
  R-compatibility here and publishing a "replication" gets a silently wrong result.
- `r*` cannot be tested against R golden vectors; it is tested for reproducibility,
  stream independence, thread safety, and goodness-of-fit against accudist's own `p*`.
