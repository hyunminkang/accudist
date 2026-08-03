---
id: adr-0002
title: "ADR-0002: Docs and implementation in separate repos"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0002 — Repo topology

## Context

`accudist.design` existed first, holding only a README, a LICENSE, and a scratch copy
of `statslabs/rmath` under a gitignored `tmp/`.

## Decision

`accudist.design` stays specifications only. Agents scaffold `../accudist` as the
GPL-2+ implementation repo. `functions.toml` is authored here and copied verbatim there.

## Rejected

| Option | Why not |
|---|---|
| Single repo | The name says "design", and the whole repo would have to become GPL-2+ — including prose that contains no GPL code. |
| Git submodule | Detached HEADs and forgotten pointer bumps; AI agents handle submodules poorly. |

## Consequences

- The spec can be reviewed and versioned independently of the code it specifies.
- `functions.toml` exists in two places. Mitigated by CI (`check_inventory.py`) and by
  the rule that it is only ever *generated* here, never hand-edited there.
