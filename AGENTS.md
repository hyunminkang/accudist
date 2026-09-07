# AGENTS.md

accudist wraps R 4.5.2's `nmath` C library as NumPy ufuncs and exposes it with R's
names, argument order and defaults. The design rationale lives in the sibling
repository `accudist.design` (branch `design` of this repo); this file is the
short operational summary.

## Rules

1. **Vendored C is pristine.** `vendor/nmath/` is extracted from the R tarball by
   `tools/sync_rmath.py`; the only modifications are `vendor/patches/*.patch`.
2. **`functions.toml` drives codegen.** `tools/regen.py` writes
   `src/_ufuncs_generated.c`, `accudist/_api.py`, `accudist/rmath.py` and
   `docs/api-reference.md`, and validates every C call against `Rmath.h`.
   `python tools/regen.py --check` must be clean before committing.
3. **The C layer never prints and never exits.** Patch 0001 routes
   `MATHLIB_ERROR`/`MATHLIB_WARNING`/`ML_WARNING` into `src/accudist_shim.c`;
   patch 0002 makes every allocation-failure site return.
4. **`log=` is the only spelling** of the log-scale flag, for d/p/q/r alike.
5. **Correctness bar: eight significant digits** against R 4.5.2 (`rel_tol=1e-8`)
   on the grids in `tests/data/`. Not bit-exactness; not every platform.
6. **Do not invent numerics.** If accudist disagrees with R, the wrapper is wrong
   until proven otherwise.

## Workflow

```bash
uv venv && uv pip install -e . --no-build-isolation numpy setuptools pytest hypothesis scipy mpmath
python tools/regen.py --check
pytest -q                      # offline; reference data is committed
python tools/gen_reference.py  # only when the grids change (needs R 4.5.2)
```

## Layout

| path | role |
|---|---|
| `vendor/nmath/` | R 4.5.2 `src/nmath` + headers, patched only via `vendor/patches/` |
| `src/accudist_shim.{h,c}` | thread-local error word, message buffer, `calloc` hook |
| `src/_ufuncsmodule.c` | module init, RNG state, bespoke entry points |
| `src/_ufuncs_generated.c` | generated: one ufunc per `Rmath.h` symbol |
| `accudist/_api.py` | generated: public wrappers |
| `accudist/_core.py`, `_errstate.py`, `_bespoke.py` | hand-written helpers |
| `accudist/compat/` | scipy-shaped shim; imports only the public API |
| `tools/` | `sync_rmath.py`, `regen.py`, `grids.py`, `gen_reference.{py,R}`, `check_inventory.py` |
| `tests/data/*.json` | R 4.5.2 reference values (decimal, 17 significant digits) |
