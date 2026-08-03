---
id: adr-0017
title: "ADR-0017: Broad wheel matrix including free-threaded builds"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0017 — Release matrix

## Context

"`pip install accudist` just works" is a stated goal. Free-threaded CPython is only
safe once the wilcox/signrank cache statics and the RNG globals are lock-guarded —
work that correctness requires anyway.

## Decision

cibuildwheel for CPython 3.10–3.14 on manylinux and musllinux (x86_64, aarch64),
macOS (x86_64, arm64) and Windows (AMD64), plus 3.13t/3.14t free-threaded. sdist always
published. Build against NumPy 2.x headers; runtime `numpy>=1.25`.

## Rejected

| Option | Why not |
|---|---|
| Mainstream only (3.11–3.13, no musl, no free-threading) | Alpine/Docker users and free-threading adopters fall back to source builds needing a compiler. |
| sdist only | Directly contradicts `pip install accudist`; most Windows users have no toolchain. |

## Consequences

- Free-threaded targets stay disabled until both locks exist (M4), rather than shipping
  something unsafe.
- PyPy is skipped: NumPy C-API ufuncs are not worth the effort there.
- The sdist must build offline — `vendor/nmath/` is committed, never downloaded at
  build time.
