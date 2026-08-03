# AGENTS.md — accudist

**Status: NORMATIVE.** This file and every `docs/NN-*.md` are instructions. Files under
`docs/adr/` and `docs/appendix/` are background — read them for *why*, never implement
from them.

You are building **accudist**, a Python package that provides probability distribution
functions with R-grade numerical precision, by wrapping R's own `nmath` C library as
NumPy ufuncs.

---

## 0. Read this first

This repo (`accudist.design`) contains **only specifications**. It contains no package
code and never will.

**The implementation lives in a sibling repo `../accudist`, which you create.**
See [docs/09-build-release.md](docs/09-build-release.md#repo-scaffold) for the scaffold.

| | `accudist.design` (here) | `accudist` (you create) |
|---|---|---|
| Contents | AGENTS.md, docs/, functions.toml | package source, vendored C, tests |
| License | CC-BY-4.0 | **GPL-2.0-or-later** |
| Contains GPL code | no | yes (vendored nmath) |

---

## 1. What problem this solves

`scipy.stats` underflows to `-inf` in tail regions where R returns finite, correct
values, and its quantile functions accept no log-scale input at all. Measured on
scipy 1.17.1 vs R 4.5.2:

| call | R 4.5.2 | scipy 1.17.1 |
|---|---|---|
| `pbinom(900, 1000, 1/6, lower=F, log=T)` | `-1312.688` | `-inf` |
| `ppois(200, 0.1, lower=F, log=T)` | `-1331.454` | `-inf` |
| `pgamma(1e5, 2, lower=F, log=T)` | `-99988.49` | `-inf` |
| `pnbinom(1e5, 10, 0.5, lower=F, log=T)` | `-69230.83` | `-inf` |
| `qnorm(-1000, log.p=TRUE)` | `-44.6157` | no `log_p` argument exists |
| `qbeta(-1000, 0.5, 0.5, log.p=TRUE)` | `1.11e-308` | `0.0` |

Full evidence, including the cases where scipy is *fine*, is in
[docs/appendix/scipy-gap-evidence.md](docs/appendix/scipy-gap-evidence.md).

---

## 2. The five invariants

These override any local reasoning. If a change would violate one, stop and write an ADR.

1. **Bit-exactness is the contract.** `accudist.f(...)` returns the same 64 bits as
   R 4.5.2's `f(...)` for the same inputs. The only sanctioned exceptions are
   human-reviewed entries in `tests/deviations.toml`. **You may propose a deviation;
   you may never ship one.** See
   [docs/08-testing.md](docs/08-testing.md#the-deviation-review-process).

2. **Vendored C is pristine.** Never edit a file under `vendor/nmath/` in place. Every
   change is a numbered patch in `vendor/patches/` applied by the sync script, so
   upgrading R stays mechanical. See [docs/02-vendoring.md](docs/02-vendoring.md).

3. **`functions.toml` is the single source of truth.** The C ufunc registrations, the
   `.pyi` stubs, the docs tables, and the test manifest are all *generated* from it.
   Never hand-edit a generated file. See [docs/03-codegen-spec.md](docs/03-codegen-spec.md).

4. **The C layer never prints and never exits.** `MATHLIB_ERROR`'s `exit(1)` and
   `MATHLIB_WARNING`'s `printf` are both replaced before anything else compiles.
   See [docs/05-errors.md](docs/05-errors.md).

5. **`log=` is the only spelling.** Not `log_p`, not `logp`, for any of d/p/q/r.
   See [docs/04-api-reference.md](docs/04-api-reference.md).

---

## 3. Routing table

Find your task; read only what it points to.

| Your task | Read |
|---|---|
| Starting from nothing / setting up the repo | [09-build-release.md](docs/09-build-release.md), then [10-milestones.md](docs/10-milestones.md) |
| Getting nmath sources in, or bumping the R version | [02-vendoring.md](docs/02-vendoring.md) |
| Adding or changing a distribution function | [03-codegen-spec.md](docs/03-codegen-spec.md) + `docs/functions.toml` |
| Changing a public signature, name, or default | [04-api-reference.md](docs/04-api-reference.md) |
| Anything about warnings, NaN, or error state | [05-errors.md](docs/05-errors.md) |
| Anything touching `r*`, seeds, or threads | [06-rng.md](docs/06-rng.md) |
| Working on the scipy drop-in shim | [07-compat-layer.md](docs/07-compat-layer.md) |
| Writing tests, or a test is failing | [08-testing.md](docs/08-testing.md) |
| Build, wheels, CI, PyPI | [09-build-release.md](docs/09-build-release.md) |
| "What do I do next?" | [10-milestones.md](docs/10-milestones.md) |
| Understanding module boundaries | [01-architecture.md](docs/01-architecture.md) |
| "Why was it done this way?" | [docs/adr/](docs/adr/) — background only |

---

## 4. Hard rules

- **Do not invent numerics.** You are wrapping R's algorithms, not writing your own.
  nmath is 25+ years old and exercised by every R user; a discrepancy is almost
  certainly a bug in your wrapper, not in R. If you genuinely believe R is wrong, write
  a candidate to `tests/deviations.pending.toml`, **leave the implementation matching
  R**, and stop — a human decides. See
  [docs/08-testing.md](docs/08-testing.md#the-deviation-review-process).
- **Do not add a function that is not in `functions.toml`.** The `[[excluded]]` entries
  are excluded deliberately, each with a reason. To add one, write an ADR first.
- **Do not reorder `c_args`.** It is the order the *C symbol* expects, which is not
  always the public order. `ptukey`/`qtukey` genuinely swap two arguments; see
  [docs/04-api-reference.md](docs/04-api-reference.md#argument-order-hazards).
- **Do not skip M1.** Every hard problem in this project lives in the first milestone.
  Fill the function table only after one function works end to end.
- **Do not weaken a test to make it pass.** A bit-exact failure is a real bug until a
  human says otherwise.
- **Do not vendor anything Apache-2.0 licensed.** It is incompatible with GPL-2.

---

## 5. Verification loop

Before claiming any milestone complete:

```bash
python tools/check_inventory.py     # functions.toml agrees with Rmath.h
python tools/regen.py --check       # no generated file is stale
pytest -q                           # incl. bit-exact golden vectors
pytest -q -m scipy_gap              # the cases scipy gets wrong
python -c "import accudist; print(accudist.__version__)"
```

`tools/check_inventory.py` must report zero unaccounted symbols and zero references to
C symbols that are declared but not defined. Both failure modes are real: `rnbeta` is
declared in `Rmath.h` and implemented nowhere.

---

## 6. Glossary

| Term | Meaning |
|---|---|
| **nmath** | R's C math library, `src/nmath` in the R source tree |
| **standalone Rmath** | nmath built without the R interpreter (`-DMATHLIB_STANDALONE`) |
| **d / p / q / r** | density, CDF, quantile, random — R's naming convention |
| **`lower_tail`** | `False` gives the survival function, computed directly, not as `1 - cdf` |
| **`log`** | results on the natural-log scale; the whole reason this package exists |
| **`ncp`** | non-centrality parameter; `None` means "use the central algorithm" |
| **deviation** | a sanctioned, gated, recorded departure from bit-exactness with R |
| **golden vector** | a reference value generated by R and committed as raw 64-bit hex |
