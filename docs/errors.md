# Warnings and errors

## What nmath does, and what accudist does instead

R's `nmath` signals problems in three ways, none of which is acceptable inside a
Python extension:

| nmath | standalone behaviour | accudist |
|---|---|---|
| `ML_WARNING(ME_DOMAIN)` and friends | returns `NaN`, prints nothing | records a flag; the wrapper warns or raises per `errstate` |
| `MATHLIB_WARNING("...")` | `printf` to **stdout** | records the message; emitted as an `AccudistWarning` with R's own text |
| `MATHLIB_ERROR("...")` | `printf`; **`exit(1)`** | records a flag and returns `NaN`; the wrapper raises `MemoryError` |

The C layer never prints and never exits. Both patches that achieve this are in
`vendor/patches/`, and the test-suite runs every warning path in a subprocess
and asserts that stdout and stderr stay empty.

## Default policy

| condition | default | class |
|---|---|---|
| allocation failure (`MATHLIB_ERROR`) | **always raises** `MemoryError`, not configurable | |
| domain (`argument out of domain`) | warn | `AccudistDomainWarning` |
| range | warn | `AccudistRangeWarning` |
| convergence failure | warn | `AccudistConvergenceWarning` |
| precision loss | ignore | `AccudistPrecisionWarning` |
| underflow | ignore | `AccudistUnderflowWarning` |
| free-text nmath message (e.g. `'k' (2.40) must be integer, rounded to 2`) | warn | `AccudistWarning` |

Precision and underflow are ignored by default because nmath raises them
routinely in correct operation and R itself does not surface them.

All warning classes derive from `AccudistWarning` (a `RuntimeWarning`); the
exception classes `AccudistDomainError`, `AccudistRangeError`,
`AccudistConvergenceError`, ... derive from `AccudistError`, a `ValueError`, so
existing `except ValueError` handlers keep working.

## `accudist.errstate`

```python
with ad.errstate(domain="raise"):
    ad.qbinom(0.5, -1, 0.5)          # AccudistDomainError

with ad.errstate(all="ignore"):
    ad.qbinom(0.5, -1, 0.5)          # nan, silent

@ad.errstate(message="ignore")       # usable as a decorator
def f(): ...

ad.get_errstate()                    # the active policy as a dict
```

Categories: `domain`, `range`, `noconv`, `precision`, `underflow`, `message`;
actions: `'ignore'`, `'warn'`, `'raise'`. `all=` sets every category first. State
is thread-local and nesting restores correctly.

## Granularity

The flag word is cleared at the start of every call and read once at the end, so
it reports *whether any element* hit a condition, not which one. That is the
price of running the loop with the GIL released; per-element reporting would
need Python callbacks inside the C loop.

## Allocation failures

`wilcox`, `signrank`, the Bessel functions and `rmultinom` allocate. If that
fails, nmath's original code would print and `exit(1)`, killing the interpreter.
accudist raises `MemoryError` instead. The test-suite proves this by injecting a
failure into the allocator (`_ufuncs._set_fail_calloc_after`).

`rmultinom` also uses `MATHLIB_ERROR` for a genuine argument error, a
probability vector that does not sum to one; accudist reports that as a
`ValueError` with R's message, not as `MemoryError`.

## Caches

`d/p/qwilcox` and `d/p/qsignrank` build a distribution table in process-wide
static storage. accudist guards every such call with a lock (so they serialise
across threads) and frees the tables at interpreter exit. Call
`accudist.free_caches()` to release the memory earlier; the tables grow with the
sample sizes `m`, `n`.
