---
id: adr-0006
title: "ADR-0006: R-flat core plus a partial scipy shim"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0006 — API surface

## Context

The stated goal is to replace `scipy.stats.*`, but the requested API was R-style flat
functions.

## Decision

`accudist.ppois(...)` is the primary, fully supported API. `accudist.compat` adds
scipy-shaped objects covering 11 core methods, documented as deliberately partial.

## Rejected

| Option | Why not |
|---|---|
| R-flat only | Migrating a scipy codebase means rewriting every call site; "replaces scipy.stats" stays aspirational. |
| Full `rv_continuous`/`rv_discrete` drop-in | Enormous surface, most of it (`fit`, `expect`, `moment`, `entropy`) unrelated to precision. High risk of stalling on scaffolding instead of shipping the thing that matters. |

## Consequences

- One-line migration for the calls where precision actually differs.
- Every absent method must raise `NotImplementedError` with a helpful message —
  asserted in tests so it can't rot.
- The shim may import only the public API, keeping it honest.
