---
id: adr-0012
title: "ADR-0012: Phase by machinery, not by distribution"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0012 — Phasing

## Context

Codegen makes adding a table-shaped function nearly free. The real cost is the
machinery, plus the functions that do not fit the table (`r*`, wilcox/signrank
allocation, the compat shim).

## Decision

M1 builds the entire stack for one function. M2 fills the table. M3–M6 handle the
awkward cases, RNG, compat, and release.

## Rejected

| Option | Why not |
|---|---|
| Phase by distribution family, precision-first | Gets value to users sooner, but the machinery still has to be right on day one — M1's risk doesn't go away, it just becomes less visible. |
| Single big-bang implementation | No feedback until the end; a wrong foundational choice (ufunc flag layout, errstate) means rewriting 150 functions instead of one. |

## Consequences

- M1 will take disproportionately long. That is the design working, not a problem.
- After M1, M2 is bulk data entry an agent can grind through reliably.
