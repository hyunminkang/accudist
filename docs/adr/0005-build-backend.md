---
id: adr-0005
title: "ADR-0005: meson-python as the build backend"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0005 — Build backend

## Context

The build compiles ~130 vendored C files, runs a codegen step, and links against
NumPy headers, while staying `pip install`- and `uv pip install`-clean.

## Decision

**meson-python**. `custom_target()` models "functions.toml → generated sources →
extension" as a real dependency graph.

## Rejected

| Option | Why not |
|---|---|
| scikit-build-core (CMake) | We re-vendor from R's autotools tarball, so the statslabs `CMakeLists.txt` is not actually inherited. CMake's NumPy integration is less direct. |
| setuptools + `Extension` | No real dependency graph, so stale generated files bite; slow serial builds; awkward editable installs with C extensions. |

## Consequences

- Meson is a new DSL for contributors; scipy's `meson.build` is a directly copyable
  reference.
- Incremental and parallel builds are correct by construction; editable installs rebuild
  automatically.
