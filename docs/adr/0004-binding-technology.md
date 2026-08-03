---
id: adr-0004
title: "ADR-0004: Code-generated NumPy ufuncs in C"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0004 — Binding technology

## Context

All ~150 nmath entry points are scalar `double → double` with trailing `int` flags.
That makes this a code-generation problem far more than a binding problem.

## Decision

A declarative `functions.toml` drives a build-time generator that emits the C ufunc
registrations, the Python wrappers, the `.pyi` stubs, and the test manifest. This is
the architecture `scipy.special` uses.

## Rejected

| Option | Why not |
|---|---|
| Cython `@cython.ufunc` | Less machinery, but adds a build dependency, emits very large C, gives less control over type signatures and error paths — and you still want a spec table for stubs and docs, so codegen returns anyway. |
| nanobind / pybind11 | Pulls a C++ toolchain in for a pure-C library, and its vectorization story is weaker than a real ufunc. |
| cffi / ctypes | ~1–10 µs per scalar call and no vectorization — roughly 100× slower than scipy on arrays. |

## Consequences

- Broadcasting, `out=`, dtype casting and `nogil` inner loops all come free from NumPy.
- ~300 lines of template machinery to write once in M1.
- Flags are ufunc *inputs*, not specializations: the C function takes them as arguments
  regardless, so a specialized variant would have nothing to specialize away.
