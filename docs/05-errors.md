---
id: errors
title: Errors, warnings, and error state
status: normative
audience: agents
updated: 2026-08-02
---

# 05 — Errors, warnings, and error state

## The problem

nmath signals trouble in three ways, none of which is acceptable inside a Python
extension:

| nmath mechanism | Standalone behaviour | Why it's unacceptable |
|---|---|---|
| `ML_ERR_return_NAN` | returns `NaN` silently | invisible; fine as a *default*, bad as the only option |
| `MATHLIB_WARNING(...)` | `printf(...)` to **stdout** | corrupts piped program output |
| `MATHLIB_ERROR(...)` | `printf(...); exit(1);` | **kills the interpreter** |

`MATHLIB_ERROR` is reachable in normal use: `wilcox.c` (4 sites), `signrank.c`,
`bessel_{i,j,k,y}.c`, `rmultinom.c`, `snorm.c` — all on allocation failure, which large
`m`/`n` will genuinely trigger.

## The design

A **thread-local error word**, set in C, decoded once per call in Python.

```c
/* src/accudist_shim.h */
typedef enum {
    ACCUDIST_OK        = 0,
    ACCUDIST_DOMAIN    = 1 << 0,   /* ME_DOMAIN    */
    ACCUDIST_RANGE     = 1 << 1,   /* ME_RANGE     */
    ACCUDIST_NOCONV    = 1 << 2,   /* ME_NOCONV    */
    ACCUDIST_PRECISION = 1 << 3,   /* ME_PRECISION */
    ACCUDIST_UNDERFLOW = 1 << 4,   /* ME_UNDERFLOW */
    ACCUDIST_ALLOC     = 1 << 5    /* was MATHLIB_ERROR */
} accudist_flag;

extern _Thread_local unsigned accudist_errword;

#define accudist_set_flag(f)   (accudist_errword |= (unsigned)(f))
#define accudist_warn(...)     accudist_set_flag(ACCUDIST_RANGE)
#define accudist_fatal(...)    accudist_set_flag(ACCUDIST_ALLOC)
```

Setting a bit is a single thread-local OR — safe with the GIL released, and cheap
enough that it never appears in a profile.

`accudist_fatal` **returns**; it does not exit. The nmath call site then falls through
to its normal `ML_NAN` path, and the Python wrapper converts the recorded
`ACCUDIST_ALLOC` bit into `MemoryError`.

> The flag word is *sticky within a call and cleared at its start*. It reports "did any
> element hit this condition", not which one or how many. That is a deliberate
> trade: per-element reporting is impossible once the loop is `nogil`.

## The Python side

```python
with _errstate.capture("ppois") as c:      # clears the word
    r = _ufuncs.ppois(q, lam, lt, lg)
c.check()                                  # decodes, then warns / raises / ignores
```

### Default policy

| flag | default | message |
|---|---|---|
| `ACCUDIST_ALLOC` | **always raises `MemoryError`** — not configurable | `accudist.<fn>: allocation failed` |
| `ACCUDIST_DOMAIN` | `warn` → `AccudistDomainWarning` | `argument out of domain in 'ppois'` |
| `ACCUDIST_RANGE` | `warn` → `AccudistRangeWarning` | `value out of range in 'ppois'` |
| `ACCUDIST_NOCONV` | `warn` → `AccudistConvergenceWarning` | `convergence failed in 'qtukey'` |
| `ACCUDIST_PRECISION` | `ignore` | `full precision may not have been achieved` |
| `ACCUDIST_UNDERFLOW` | `ignore` | `underflow occurred` |

`PRECISION` and `UNDERFLOW` default to `ignore` because nmath raises them routinely in
correct operation; warning on them would train users to filter everything.

`ALLOC` is deliberately not configurable. Silencing a failed allocation converts a
resource problem into wrong numbers.

### `accudist.errstate`

```python
ad.errstate(domain='warn', range='warn', noconv='warn',
            precision='ignore', underflow='ignore', all=None)
```

Each takes `'ignore'`, `'warn'`, or `'raise'`. `all=` sets every configurable category
at once. Usable as a context manager or a decorator; state is thread-local; nesting
restores correctly.

```python
with ad.errstate(domain='raise'):
    ad.qbinom(0.5, -1, 0.5)          # ValueError
with ad.errstate(all='ignore'):
    ad.qbinom(0.5, -1, 0.5)          # nan, silent
```

Exception types: `AccudistDomainError`, `AccudistRangeError`,
`AccudistConvergenceError` — all subclassing `ValueError` so existing
`except ValueError` handlers keep working.

---

## The wilcox / signrank caches

`wilcox.c` and `signrank.c` cache the distribution table in file-static storage:

```c
static double **w;  static int allocated_m, allocated_n;   /* wilcox.c   */
static double *w;   static int allocated_n;                /* signrank.c */
```

Three consequences, all mandatory to handle:

1. **Not thread-safe.** Two threads with different `m`/`n` will free and reallocate
   under each other. Every `*wilcox` and `*signrank` call takes a dedicated
   `accudist_cache_lock` — a real lock, held across the whole ufunc call, *not* just
   the allocation.
2. **They leak.** Expose `ad.free_caches()`, and register `wilcox_free()` /
   `signrank_free()` via `atexit` and in the module's `m_free` slot.
3. **`WILCOX_MAX` is 50.** `m` or `n` above 50 hits the allocation path hard —
   the table is `O(m·n·max)` doubles. Document the memory cost; do not silently cap.

Because the lock is held for the whole call, these functions do **not** scale across
threads. That is correct and preferable to corruption. Note it in the docstrings.

## Free-threaded builds

Under free-threaded CPython (3.13t/3.14t) the GIL no longer serialises anything:

- `d`/`p`/`q` ufuncs are pure functions of their arguments — safe, no locking.
- `wilcox`/`signrank` — `accudist_cache_lock`, as above.
- everything `r*` — the RNG lock, see [06-rng.md](06-rng.md).
- the error word is `_Thread_local` — safe by construction.

Declare `Py_mod_gil = Py_MOD_GIL_NOT_USED` only after all three locks exist.

## Testing

- Every flag has a test that provokes it (`tests/test_errstate.py`).
- A test asserts nothing is written to stdout or stderr during the whole suite —
  this is the regression guard for the `printf` patch.
- A test calls `psignrank` with `n` large enough to fail allocation under a
  `RLIMIT_AS` cap and asserts `MemoryError`, **not** a crash. This is the regression
  guard for the `exit(1)` patch, and it is the single most important test in the suite.
- A threaded test hammers `pwilcox` from 8 threads with different `m`/`n` and asserts
  results match the single-threaded golden values.
