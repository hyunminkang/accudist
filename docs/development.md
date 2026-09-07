# Development and release

## Layout

| path | role |
|---|---|
| `functions.toml` | the inventory: every public function, its parameters, defaults, flags, dispatch and C symbol |
| `tools/regen.py` | generates `src/_ufuncs_generated.c`, `accudist/_api.py`, `accudist/rmath.py`, `docs/api-reference.md` from the inventory and validates every C call against `Rmath.h` |
| `tools/check_inventory.py` | every symbol in `Rmath.h` is a function, bespoke wrapper, RNG primitive or documented exclusion |
| `vendor/nmath/` | R 4.5.2 `src/nmath` + headers, pristine except for `vendor/patches/` |
| `tools/sync_rmath.py` | downloads the pinned R tarball (`vendor/VENDOR.toml`), verifies its SHA-256, extracts, applies the patches |
| `src/accudist_shim.{h,c}` | thread-local error word and message buffer, `calloc` hook |
| `src/_ufuncsmodule.c` | module init, RNG state, bespoke entry points |
| `accudist/_core.py`, `_errstate.py`, `_bespoke.py` | hand-written Python helpers |
| `accudist/compat/` | the scipy-shaped shim (imports only the public API) |
| `tools/grids.py`, `tools/gen_reference.{py,R}` | designed evaluation grids and the R reference generator |
| `tests/data/*.json` | R 4.5.2 reference values (decimal, 17 significant digits) |
| `tests/reference_tolerances.py` | the documented regions with relaxed tolerance |

## Workflow

```console
uv venv && source .venv/bin/activate
uv pip install setuptools numpy pytest hypothesis scipy mpmath
uv pip install --no-build-isolation -e .
python tools/regen.py --check        # generated files are up to date
python tools/check_inventory.py      # Rmath.h fully accounted for
pytest -q                            # offline; ~330 tests, a few seconds
pytest -q -m "not slow"              # skip the thread stress test
```

Generated files are committed so that building from the sdist needs no tooling
beyond a C compiler. CI fails if they are stale.

### Adding or changing a function

1. Edit `functions.toml` (public parameter order in `params`, C order in `c_args`).
2. `python tools/regen.py` (fails if the C arity disagrees with `Rmath.h`).
3. Add a grid in `tools/grids.py` if needed and run
   `python tools/gen_reference.py <name>` (needs R 4.5.2 on `PATH`).
4. `pytest -q -k <name>`.

### Bumping R

1. Update version, URL and SHA-256 in `vendor/VENDOR.toml`.
2. `python tools/sync_rmath.py`; fix any patch that no longer applies (never edit
   `vendor/nmath/` in place).
3. `python tools/check_inventory.py` for new or removed symbols.
4. Under the new R: `python tools/gen_reference.py`. Any changed reference value is
   a finding; investigate before committing.
5. Record it in `CHANGELOG.md`.

## Build flags

| flag | why |
|---|---|
| `-DMATHLIB_STANDALONE -DHAVE_CONFIG_H` | nmath's standalone mode with our `src/config.h` |
| `-ffp-contract=off` | no fused multiply-add, so results do not depend on the CPU |
| `-fvisibility=hidden` | only `PyInit__ufuncs` is exported; nmath's plain C names cannot collide with another Rmath in the process |
| `-O2`, never `-ffast-math` | nmath relies on IEEE `Inf`/`NaN` semantics |

## Release

Wheels are built by `.github/workflows/wheels.yml` with cibuildwheel for CPython
3.10 to 3.14 on manylinux x86_64/aarch64, macOS x86_64/arm64 and Windows AMD64,
tested in a clean environment, and published to PyPI through trusted publishing
(no API token in the repository) when a `v*` tag is pushed. The sdist is built
and installed offline in the same workflow.

1. Update `version` in `pyproject.toml` and `CHANGELOG.md`.
2. `git tag v0.1.0 && git push --tags`.
3. The `pypi` environment on GitHub must be configured as a trusted publisher on
   PyPI for the workflow to publish.

Versioning: `MAJOR.MINOR.PATCH`; `accudist.__r_version__` reports the vendored R.
An R bump that changes any reference value is at least a minor release.
