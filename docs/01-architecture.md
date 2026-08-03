---
id: architecture
title: Architecture
status: normative
audience: agents
updated: 2026-08-02
---

# 01 — Architecture

## Layer diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ accudist.compat            scipy-shaped shim (M5)                │  ← optional
│   binom, poisson, norm, ...  .pmf .cdf .sf .logsf .ppf .isf      │
└──────────────────────────────┬───────────────────────────────────┘
                               │ imports only the public API below
┌──────────────────────────────▼───────────────────────────────────┐
│ accudist                   PUBLIC API (M2)                       │
│   ppois(q, lambda_, lower_tail=True, log=False)                  │
│   pchisq(q, df, ncp=None, ...)      ← Python-level dispatch      │
│   errstate(...)   RNG(...)   set_seed(...)                       │
│   Thin, pure Python: defaults, kwargs, dispatch, error checks     │
└──────────────────────────────┬───────────────────────────────────┘
                               │ selects one ufunc, calls it once
┌──────────────────────────────▼───────────────────────────────────┐
│ accudist._ufuncs           GENERATED C EXTENSION (M1)            │
│   one NumPy ufunc per C symbol; flags are trailing int inputs    │
│   inner loops nogil; sets thread-local error flags on the way out│
└──────────────────────────────┬───────────────────────────────────┘
                               │ calls
┌──────────────────────────────▼───────────────────────────────────┐
│ vendor/nmath               R 4.5.2 C SOURCES, PRISTINE           │
│   + vendor/patches/        the only sanctioned modifications     │
│   + src/accudist_shim.h    replaces MATHLIB_ERROR / _WARNING     │
└──────────────────────────────────────────────────────────────────┘
```

## Module map

| Module | Kind | Purpose |
|---|---|---|
| `accudist/__init__.py` | hand-written | re-exports the public API; nothing else |
| `accudist/_api.py` | **generated** | one wrapper function per `functions.toml` entry |
| `accudist/_generated.pyi` | **generated** | type stubs for the above |
| `accudist/_dispatch.py` | hand-written | `ncp`, `prob`/`mu`, `rate`/`scale` resolution helpers |
| `accudist/_errstate.py` | hand-written | `errstate` context manager, flag decoding |
| `accudist/_rng.py` | hand-written | `RNG` class, module lock, `set_seed`/`get_seed` |
| `accudist/_bespoke.py` | hand-written | `pnorm_both`, `lgammafn_sign`, `rmultinom`, `logspace_sum` |
| `accudist/rmath.py` | **generated** | raw 1:1 C signatures, positional int flags |
| `accudist/compat/` | hand-written | scipy-shaped shim (M5) |
| `accudist/_ufuncs.c` | **generated** | ufunc registration + inner loops |
| `src/accudist_shim.{h,c}` | hand-written | error/warning redirection, cache lifecycle, lock |
| `vendor/nmath/**` | **vendored** | never edited in place |
| `vendor/patches/*.patch` | hand-written | the only sanctioned edits to the above |
| `tools/regen.py` | hand-written | runs codegen; `--check` verifies freshness |

## Import rules

These are enforced by a test (`tests/test_layering.py`).

- `accudist._ufuncs` imports nothing from Python. It is a leaf.
- `accudist._api` may import `_ufuncs`, `_dispatch`, `_errstate`. Nothing else.
- `accudist.compat` may import only the public `accudist` namespace — never `_ufuncs`
  directly. This keeps the shim honest: if the public API can't express something,
  the shim can't either.
- Nothing imports `scipy`. Not even the compat layer. scipy appears only as a *test*
  dependency, for the gap-regression suite.

## Why the Python wrapper is thin

The wrapper does exactly four things per call:

1. resolve defaults and keyword names
2. resolve dispatch (`ncp is None`? `mu` given? `rate` or `scale`?)
3. call **one** ufunc, passing `lower_tail` and `log` as int inputs
4. check the thread-local error word once, and warn or raise per `errstate`

It must **not** loop over elements, validate array contents, or reimplement
broadcasting. NumPy already does all of that, correctly and in C.

Cost: roughly 1 µs of Python overhead per call, which dominates for scalar arguments
and vanishes for arrays. Users who need the scalar fast path get the raw ufunc:

```python
from accudist._ufuncs import ppois      # no defaults, no kwargs, no errstate
ppois(200.0, 0.1, 0, 1)
```

This is documented but not sugared — see [04-api-reference.md](04-api-reference.md#escape-hatches).

## Data flow for one call

```
ad.pchisq(3.0, df=5, ncp=1.5, lower_tail=False, log=True)
  │
  ├─ _dispatch.resolve_ncp(ncp=1.5)        → "call_ncp"
  ├─ select _ufuncs.pnchisq                (not _ufuncs.pchisq)
  ├─ _ufuncs.pnchisq(3.0, 5.0, 1.5, 0, 1)  ← c_args order from functions.toml
  │     └─ nogil loop → C pnchisq(...) → sets thread-local flags on ME_* events
  └─ _errstate.check("pchisq")             → warn / raise / ignore
```
