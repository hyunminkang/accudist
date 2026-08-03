---
id: adr-0007
title: "ADR-0007: Mirror R's signatures; unify on log="
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0007 — Signature conventions

## Context

Two collisions force choices: R's Poisson parameter is `lambda`, a Python keyword;
and R uses `log=` for `d*`/`r*` but `log.p=` for `p*`/`q*`.

## Decision

- Mirror R's argument order, names and defaults.
- `lambda` → `lambda_` (PEP 8 trailing underscore), the only such rename.
- **`log=` everywhere**, for d/p/q/r alike. `log_p=` raises `TypeError`.

## Rejected

| Option | Why not |
|---|---|
| Mirror R's `log=`/`log.p=` asymmetry exactly | Two names for one concept is a permanent papercut. |
| Unify on `log_p=` | Considered; the opposite was chosen — `log=` is shorter and matches the `d*` spelling users type most. |
| `log=` canonical with `log_p=` as a soft alias | Reintroduces the two-spelling problem, doubles stub/doc/test surface, and such an alias is never actually removed. |
| scipy-leaning names (`mu`, `loc`, `scale`) | Then *neither* R nor scipy users get a clean translation, and the docs carry a bidirectional mapping forever. |

## Consequences

- R code translates character-for-character except for `log.p` → `log`.
- This inverts the `log_p=` spelling used in the original project request; it was
  confirmed explicitly before adoption.
