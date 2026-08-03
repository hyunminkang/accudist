---
id: adr-0008
title: "ADR-0008: ncp=None sentinel dispatch"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0008 — Non-central dispatch

## Context

R's `pchisq(q, df, ncp)` dispatches on `missing(ncp)`, not on value:
`.Call(C_pchisq, ...)` when absent, `.Call(C_pnchisq, ...)` when present — so
`ncp = 0` takes the non-central path and gives a slightly different answer. Rmath's
C API exposes the two as separate symbols.

## Decision

Mirror R's user level. `ncp=None` is the sentinel for "central". The raw C names stay
reachable via `accudist.rmath`.

## Rejected

| Option | Why not |
|---|---|
| Expose only the C-level names | R code translates less directly; `pchisq(q, df, ncp)` would have no single Python equivalent. |
| R-level dispatch with no escape hatch | No way to force the non-central path explicitly, and readers of the Rmath docs won't find the names they expect. |

## Consequences

- `ncp=0.0` and `ncp=None` differ, exactly as in R. Both are pinned by golden vectors.
- Dispatch is one Python-level branch selecting a ufunc — no per-element cost.
- `r*` with `ncp` is a special case: only `rchisq` has a C implementation. `rbeta`,
  `rf`, `rt` are composed in R code and must be composed identically. `rnbeta` is
  declared in `Rmath.h` and **defined nowhere**.
