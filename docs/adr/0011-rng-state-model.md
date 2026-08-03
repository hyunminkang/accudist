---
id: adr-0011
title: "ADR-0011: Global RNG state swapped under a lock"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0011 — RNG state model

## Context

nmath's `r*` functions call `unif_rand()` with no arguments, reading two file-static
ints. Making the state explicit would mean patching every `r*` signature.

## Decision

Leave the vendored globals untouched. `accudist.RNG(i1, i2)` holds its own state; each
draw takes a module lock, `set_seed()`s its state in, runs the whole vectorised draw,
then `get_seed()`s the result back out.

## Rejected

| Option | Why not |
|---|---|
| Global state only, Rmath API mirrored | No independent streams; parallel simulation would need processes. |
| Thread-local `I1`/`I2` | `set_seed()` in the main thread would silently not affect workers — a subtle and confusing failure mode — and it patches vendored code. |

## Consequences

- Full thread safety and independent streams with **zero** patches to vendored code:
  `get_seed`/`set_seed` already exist for exactly this purpose.
- The lock is held for an entire draw, so concurrent `r*` calls serialise rather than
  interleaving into garbage. Correct, and preferable to corruption.
- Composed non-central draws must happen inside a single lock acquisition.
