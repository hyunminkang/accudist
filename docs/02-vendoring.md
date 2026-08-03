---
id: vendoring
title: Vendoring nmath from R
status: normative
audience: agents
updated: 2026-08-02
---

# 02 — Vendoring nmath from R

## Pinned version

```
R 4.5.2   (released 2025-10-31)
https://cran.r-project.org/src/base/R-4/R-4.5.2.tar.gz
```

The pin lives in `vendor/VENDOR.toml` together with the tarball SHA-256. The sync
script **must** verify the hash and refuse to proceed on mismatch.

> A local R installation ships only headers — there is no `src/nmath` under
> `R RHOME`. The tarball is the only source. Do not try to reconstruct nmath from
> an installed R.

## What to extract

From the tarball, into `vendor/nmath/`:

| From | To | Notes |
|---|---|---|
| `src/nmath/*.c` | `vendor/nmath/src/` | ~130 files; **exclude** `standalone/` for now |
| `src/nmath/*.h` | `vendor/nmath/src/` | `nmath.h`, `dpq.h`, `bessel.h` |
| `src/nmath/standalone/sRmath.h.in` | `vendor/nmath/include/Rmath.h.in` | template; see below |
| `src/include/R_ext/*.h` | `vendor/nmath/include/R_ext/` | only those actually included |

`Rmath.h` is generated from `Rmath.h.in` by substituting `@PACKAGE_VERSION@` etc.
The sync script does this substitution and writes `vendor/nmath/include/Rmath.h`,
recording the R version string in the process.

Build with `-DMATHLIB_STANDALONE`.

## Do not edit vendored files

Every required change is a numbered patch under `vendor/patches/`, applied by
`tools/sync_rmath.py` after extraction. This is invariant #2 in
[../AGENTS.md](../AGENTS.md#2-the-five-invariants) and it exists so that bumping R is
a mechanical operation rather than an archaeological one.

If a patch fails to apply after an R bump, that is the signal to review it — not to
edit the source in place.

## The required patch set

These are mandatory. Without them accudist is unusable or unsafe.

### `0001-no-exit-no-printf.patch` — **blocking**

In `MATHLIB_STANDALONE` mode, `nmath.h` defines:

```c
#define MATHLIB_ERROR(fmt,x)     { printf(fmt,x); exit(1); }
#define MATHLIB_WARNING(fmt,x)   printf(fmt,x)
```

`exit(1)` would terminate the Python interpreter. `printf` writes to **stdout**,
corrupting any program piping its output. Callers of `MATHLIB_ERROR` are real:
`bessel_i.c`, `bessel_j.c`, `bessel_k.c`, `bessel_y.c`, `wilcox.c` (four sites),
`signrank.c`, `rmultinom.c`, `snorm.c`.

The patch redirects all of them into `src/accudist_shim.h`:

```c
#define MATHLIB_ERROR(fmt, x)    accudist_fatal(fmt, x)   /* sets flag, returns */
#define MATHLIB_WARNING(fmt, x)  accudist_warn(fmt, x)    /* sets flag only     */
/* ... WARNING2..WARNING5 likewise */
```

`accudist_fatal` records `ACCUDIST_ERR_ALLOC` in the thread-local error word and
returns; the calling nmath function then falls through to returning `ML_NAN`, and the
Python wrapper converts the recorded flag into `MemoryError`. See
[05-errors.md](05-errors.md).

### `0002-ml-error-to-flags.patch`

`ML_ERROR(x, s)` formats and emits a message. Replace the body with a single
`accudist_set_flag(x)` call. The message text is reconstructed in Python from the flag
plus the calling function's name, which the wrapper already knows.

### `0003-cache-lifecycle.patch`

`wilcox.c` and `signrank.c` hold file-static caches:

```c
static double **w;  static int allocated_m, allocated_n;   /* wilcox.c   */
static double *w;   static int allocated_n;                /* signrank.c */
```

They are **not thread-safe** and leak unless freed. The patch is minimal — it only
exposes the existing `wilcox_free()` / `signrank_free()` for the shim to call. All
locking happens in `accudist_shim.c`, not in vendored code. See
[05-errors.md](05-errors.md#the-wilcox--signrank-caches).

### `0004-visibility.patch`

Ensure `attribute_hidden` resolves so internal symbols are not exported from the
extension module. Prevents symbol collisions when another extension in the same
process also links a copy of Rmath.

## Symbol aliases you will trip over

`Rmath.h` defines these macros. Generated code includes `Rmath.h`, so writing
`pnorm(...)` works — but a symbol table will show the right-hand name:

| Written | Actual symbol |
|---|---|
| `dnorm` | `dnorm4` |
| `pnorm` | `pnorm5` |
| `qnorm` | `qnorm5` |
| everything else | `Rf_<name>` |

## Declared but never defined

**`rnbeta` is declared in `Rmath.h` and implemented in no `.c` file.** Referencing it
produces a link error. R does not use it either — `rbeta(n, shape1, shape2, ncp)` is
composed in R code from `rchisq`. `functions.toml` records this as a `composed` entry.

`tools/check_inventory.py` guards against reintroducing this class of bug by resolving
every `c_symbol` in `functions.toml` against the vendored sources.

## Bumping the R version

1. Update `vendor/VENDOR.toml` (version + SHA-256).
2. `python tools/sync_rmath.py` — re-extracts, re-applies patches. Fix any patch that
   no longer applies; do not edit sources in place.
3. `python tools/check_inventory.py` — catches new, removed, or re-signatured symbols.
4. `Rscript tools/gen_reference.R` under the **new** R — regenerates golden vectors.
5. `pytest` — any diff in golden values is a *finding*, not a nuisance. Investigate
   each one before committing; an upstream accuracy fix and an upstream regression
   look identical at this stage.
6. Record the bump in `CHANGELOG.md`, listing every changed golden value.
