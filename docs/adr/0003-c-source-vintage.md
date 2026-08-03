---
id: adr-0003
title: "ADR-0003: Vendor nmath fresh from R 4.5.2"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0003 — C source vintage

## Context

`tmp/rmath` (statslabs/rmath, last commit 2018) carries R Core copyright dates of
1998–2016 — roughly R 3.4-era nmath. It has `logspace_add`, `dpois_raw` and the
`*_mu` negative-binomial variants, but **not** `ebd0`, the rewritten deviance
computation R Core landed in 4.4.0. Current R is 4.5.2.

A local R installation ships only headers; `R RHOME` contains no `src/nmath`.

## Decision

Vendor `src/nmath` from the official R 4.5.2 source tarball, pinned by version and
SHA-256 in `vendor/VENDOR.toml`, extracted by `tools/sync_rmath.py`.

## Rejected

| Option | Why not |
|---|---|
| Vendor `tmp/rmath` as-is | Frozen at ~R 3.4. "Bit-identical to R" becomes false the moment anyone checks against a modern R — and it is trivially checkable. |
| statslabs first, upgrade later | The standalone-glue cost is paid either way, just later, and the entire golden-vector corpus would need regenerating at the swap. |

## Consequences

- We write the `MATHLIB_STANDALONE` glue ourselves rather than inheriting statslabs'.
- Bumping R is a defined, scripted procedure (see [../02-vendoring.md](../02-vendoring.md)).
- `tmp/rmath` remains useful only as a reading reference and is gitignored.
