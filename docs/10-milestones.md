---
id: milestones
title: Milestones and acceptance criteria
status: normative
audience: agents
updated: 2026-08-02
---

# 10 — Milestones and acceptance criteria

Phased by **machinery**, not by distribution. Every hard problem is in M1; after that,
M2 is bulk table-filling that a single agent can grind through reliably.

Do not start a milestone until the previous one's criteria are all green.

---

## M1 — vertical slice  ⭐ all the risk lives here

Build the entire stack for **exactly one function** (`ppois`).

**Do**

1. Scaffold `../accudist` per [09-build-release.md](09-build-release.md#repo-scaffold).
2. `tools/sync_rmath.py`: download R 4.5.2, verify SHA-256, extract, apply patches
   0001–0004. See [02-vendoring.md](02-vendoring.md).
3. `src/accudist_shim.{h,c}`: thread-local error word, `accudist_fatal`,
   `accudist_warn`, both locks. See [05-errors.md](05-errors.md).
4. `tools/regen.py` emitting all four artifacts, with `ppois` alone enabled.
5. `accudist/_errstate.py` with `capture()` and `errstate()`.
6. `meson.build`; `pip install -e .` works.
7. Golden vectors for `ppois` via `tools/gen_reference.R`.
8. `tools/check_inventory.py`.

**Acceptance**

- [ ] `pip install .` and `uv pip install .` both succeed from a clean checkout
- [ ] `ad.ppois(200, 0.1, lower_tail=False, log=True)` is bit-identical to R
- [ ] `ad.ppois` broadcasts, honours `out=`, and returns `np.float64` for scalars
- [ ] ~300 golden points for `ppois` pass bit-exact
- [ ] a domain error warns via `errstate` and returns `NaN`; `errstate(domain='raise')` raises
- [ ] **the whole suite writes nothing to stdout/stderr** (the `printf` patch works)
- [ ] **a forced allocation failure raises `MemoryError` instead of killing the process**
      (the `exit(1)` patch works)
- [ ] `tools/regen.py --check` is clean; `check_inventory.py` reports 0 unaccounted
- [ ] one wheel builds locally

> If M1 takes three times longer than expected, that is normal and correct. Everything
> after it is fast *because* of it.

---

## M2 — fill the table

All central `d`/`p`/`q`/`r` plus special functions and utilities — every
`functions.toml` entry marked `milestone = "M2"`.

**Do**

1. Enable all M2 entries in `regen.py`.
2. Implement `_dispatch.py`: `ncp` sentinel, `prob`/`mu`, `rate`/`scale`.
3. Generate golden vectors for everything; build the shared grid in `tools/grids.py`.
4. Layer-2 invariant tests.
5. Layer-3 scipy-gap suite from
   [appendix/scipy-gap-evidence.md](appendix/scipy-gap-evidence.md).

**Acceptance**

- [ ] every M2 entry importable, typed, docstringed, and bit-exact on its grid
- [ ] all four `lower_tail` × `log` combinations covered per function
- [ ] `ncp=None` vs `ncp=0.0` verified to take different paths and match R in both
- [ ] `rate`/`scale` and `prob`/`mu` errors and warnings match R's behaviour
- [ ] `dexp` family verified against the `1/rate` transform
- [ ] every gap case in the appendix passes
- [ ] invariants hold under Hypothesis
- [ ] mypy clean against the generated stubs

---

## M3 — the awkward ones

Non-central dispatch targets, Tukey, Wilcoxon, signrank, Bessel, and the bespoke
wrappers.

**Do**

1. `pnchisq`/`pnbeta`/`pnt`/`pnf` and their `d`/`q` siblings.
2. `ptukey`/`qtukey` — **with the `c_args` reorder**.
3. `wilcox`/`signrank` under `accudist_cache_lock`, plus `ad.free_caches()`,
   `atexit`, and the module `m_free` slot.
4. `bessel_i`/`bessel_k` with `expon_scaled` → C `expo ∈ {1.0, 2.0}`.
5. `_bespoke.py`: `pnorm_both`, `lgammafn_sign`.

**Acceptance**

- [ ] `ad.ptukey(3.5, nmeans=5, df=20, nranges=1)` matches R — the dedicated
      argument-order regression test passes
- [ ] `pwilcox` from 8 threads with differing `m`/`n` matches single-threaded goldens
- [ ] no memory growth over 10 000 `pwilcox` calls with varying `m`/`n`
- [ ] `psignrank` at large `n` raises `MemoryError`, never crashes
- [ ] `pnorm_both` returns a 2-tuple agreeing with `pnorm(lower=T/F)`
- [ ] non-central grids bit-exact, including `ncp=0.0`

---

## M4 — random generation

See [06-rng.md](06-rng.md).

**Do**

1. `_rng.py`: `RNG` class, module lock, save/restore via `get_seed`/`set_seed`.
2. All `r*` with R's recycling semantics.
3. Composed non-central `rbeta`/`rf`/`rt` — exact draw order.
4. `rmultinom` bespoke wrapper, with the probability-sum error mapped to `ValueError`.
5. The R-incompatibility warning in every docstring, the module, and the README.

**Acceptance**

- [ ] same seed → same draws, across runs, platforms, and Python versions
- [ ] 8 threads × independent `RNG`s reproduce their single-threaded sequences
- [ ] goodness-of-fit against accudist's own `p*` passes at α = 1e-6, fixed seeds
- [ ] composed non-central draws leave the documented seed state
- [ ] `rmultinom` with probabilities not summing to 1 raises `ValueError`, not `MemoryError`
- [ ] the R-incompatibility caveat is asserted present in every `r*` docstring
- [ ] free-threaded wheels can now be enabled

---

## M5 — compat layer

See [07-compat-layer.md](07-compat-layer.md).

**Acceptance**

- [ ] the 11 supported methods work frozen and unfrozen
- [ ] every mapping in the parameterisation table agrees with scipy to `rtol=1e-12`
      where scipy is accurate
- [ ] the `geom` off-by-one, `hypergeom` reparameterisation, and `lognorm` `scale`
      traps each have a passing dedicated test
- [ ] `logpdf` Jacobian correct for every `loc`/`scale` distribution
- [ ] unimplemented methods raise `NotImplementedError` with an asserted message
- [ ] nothing under `accudist/` imports scipy (enforced by `test_layering.py`)

---

## M6 — release

**Do**

1. Full cibuildwheel matrix, trusted publishing.
2. User docs (Sphinx or mkdocs): R↔accudist mapping, the precision rationale, the
   GPL implication, the RNG caveat.
3. Benchmarks vs scipy — array throughput and scalar overhead, published honestly.
4. `CHANGELOG.md`, `NOTICE`, licence files in the wheel.

**Acceptance**

- [ ] wheels for every target install and pass their tests in a clean container
- [ ] `pip install accudist` and `uv pip install accudist` work on all three OSes
- [ ] sdist builds offline with no network
- [ ] docs state the GPL implication *and* the RNG caveat above the fold
- [ ] benchmarks published, including the ~1 µs scalar wrapper overhead — do not hide it
- [ ] `accudist.__r_version__ == "4.5.2"`

---

## Progress

| Milestone | Status |
|---|---|
| M1 vertical slice | ☐ not started |
| M2 fill the table | ☐ not started |
| M3 awkward ones | ☐ not started |
| M4 random generation | ☐ not started |
| M5 compat layer | ☐ not started |
| M6 release | ☐ not started |
