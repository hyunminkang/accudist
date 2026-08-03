---
id: adr-0014
title: "ADR-0014: Special functions keep their Rmath C names"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0014 — Special function naming

## Context

ADR-0007 says distribution functions use R's user-level names. Special functions are
awkward: R calls them `gamma`, `lgamma`, `besselI`, `psigamma`; Rmath's C API calls
them `gammafn`, `lgammafn`, `bessel_i`, `psigamma`.

## Decision

Distribution functions use R's names; **special functions use Rmath's C names**. The
rule is uniform and documented, and every such entry carries `r_equivalent` in
`functions.toml` and names the R spelling in its docstring.

## Rejected

| Option | Why not |
|---|---|
| `ad.gamma(x)` following R | Sits confusingly beside `ad.dgamma`/`ad.pgamma`, and shadows `math.gamma` for anyone doing `from accudist import *`. |
| Provide both as aliases | Doubles the surface for no gain and makes "which is canonical?" a recurring question. |

## Consequences

- `ad.gammafn(x)`, `ad.lgammafn(x)`, `ad.bessel_i(x, nu, expon_scaled=False)`.
- The R→accudist translation table in
  [../04-api-reference.md](../04-api-reference.md#r--accudist-translation) is the
  authoritative mapping and must stay complete.
