---
id: adr-0009
title: "ADR-0009: errstate with thread-local error flags"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0009 — Error handling

## Context

nmath signals problems three ways in standalone mode: silent `NaN` (`ME_DOMAIN`),
`printf` to **stdout** (`MATHLIB_WARNING`), and `printf` + **`exit(1)`**
(`MATHLIB_ERROR`, reachable from `wilcox.c`, `signrank.c`, `bessel_*.c`,
`rmultinom.c`, `snorm.c` on allocation failure). The `exit(1)` would kill the
interpreter and had to go regardless.

## Decision

`ML_ERROR`/`MATHLIB_WARNING`/`MATHLIB_ERROR` set bits in a `_Thread_local` error word.
The Python wrapper decodes it once per call and warns, raises, or ignores per
`accudist.errstate(...)`. Allocation failure always raises `MemoryError`.

## Rejected

| Option | Why not |
|---|---|
| Silent NaN like scipy.stats | Convergence failures and precision loss become invisible — uncomfortable for a library whose entire premise is numerical trustworthiness. |
| Always warn, no errstate | Only silenceable through the coarse stdlib warnings filter, and no `raise` mode for users who want failures loud. |

## Consequences

- Per-element reporting is impossible once loops are `nogil`; the flag word reports
  "did any element hit this", which is the honest granularity.
- `PRECISION` and `UNDERFLOW` default to `ignore` because nmath raises them routinely
  in correct operation.
- The C-side plumbing is nearly free now and painful to retrofit — hence M1, not later.
