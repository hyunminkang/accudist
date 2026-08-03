---
id: build
title: Build, packaging, and release
status: normative
audience: agents
updated: 2026-08-02
---

# 09 — Build, packaging, and release

## Repo scaffold

Create `../accudist` (sibling of `accudist.design`):

```
accudist/
├── LICENSE                     GPL-2.0-or-later  (NOT Apache — see ADR-0001)
├── README.md
├── CHANGELOG.md
├── AGENTS.md                   short; points at ../accudist.design/AGENTS.md
├── CLAUDE.md                   3-line pointer to AGENTS.md
├── pyproject.toml
├── meson.build
├── docs/functions.toml         copied verbatim from the design repo
├── vendor/
│   ├── VENDOR.toml             pinned R version + SHA-256
│   ├── nmath/                  extracted, pristine
│   └── patches/                0001..0004, see 02-vendoring.md
├── src/
│   ├── accudist_shim.h
│   └── accudist_shim.c
├── accudist/
│   ├── __init__.py
│   ├── _dispatch.py  _errstate.py  _rng.py  _bespoke.py
│   ├── _api.py  _generated.pyi  rmath.py  _ufuncs.c     ← all GENERATED
│   ├── py.typed
│   ├── compat/
│   └── meson.build
├── tools/
│   ├── sync_rmath.py  regen.py  check_inventory.py  grids.py
│   └── gen_reference.R
└── tests/
    ├── data/                   golden vectors (JSONL, hex)
    ├── deviations.toml          active — human-reviewed only
    ├── deviations.pending.toml  agent-written candidates; nothing reads this
    ├── ulp_waivers.toml
    └── test_*.py
```

`AGENTS.md` in the implementation repo stays short — it points here rather than
duplicating, so the two can't drift.

## `pyproject.toml`

```toml
[build-system]
requires = ["meson-python>=0.15", "numpy>=2.0"]
build-backend = "mesonpy"

[project]
name = "accudist"
description = "Probability distributions with R-grade numerical precision"
requires-python = ">=3.10"
dependencies = ["numpy>=1.25"]
license = "GPL-2.0-or-later"
license-files = ["LICENSE", "vendor/nmath/COPYING"]

[project.optional-dependencies]
test = ["pytest>=8", "hypothesis>=6", "mpmath>=1.3", "scipy>=1.11"]
```

Build against NumPy 2.x headers; the resulting wheels run against `numpy>=1.25` thanks
to NumPy 2's backward-compatible ABI. Do not pin numpy at runtime.

`scipy` and `mpmath` are **test-only**. Nothing under `accudist/` imports either.

## Meson

Model codegen as a real dependency edge so staleness is impossible:

```meson
gen = custom_target('accudist-codegen',
  input  : ['../docs/functions.toml'],
  output : ['_ufuncs.c', '_api.py', '_generated.pyi', 'rmath.py'],
  command: [py, files('../tools/regen.py'), '@INPUT@', '@OUTDIR@'],
)

py.extension_module('_ufuncs',
  [gen[0], 'accudist_shim.c'] + nmath_sources,
  include_directories : [nmath_inc, shim_inc],
  dependencies : [py_dep, np_dep, m_dep],
  c_args : ['-DMATHLIB_STANDALONE', '-ffp-contract=off'],
  install : true, subdir : 'accudist',
)
```

### Compiler flags — not optional

| flag | why |
|---|---|
| `-DMATHLIB_STANDALONE` | required by nmath |
| `-ffp-contract=off` | FMA contraction changes last bits and breaks bit-exactness |
| **never** `-ffast-math` | it breaks NaN/Inf handling, which nmath relies on throughout |
| `-O2` | `-O3` buys nothing measurable here and perturbs more last bits |
| `/fp:precise` (MSVC) | the MSVC equivalent of the first two |

Bit-exactness is a build-flag property as much as a source property. A wheel built with
`-ffast-math` would fail the suite — which is the intended behaviour.

## Wheels

`cibuildwheel`, publishing to PyPI via trusted publishing (OIDC — no API token in CI).

```yaml
CIBW_BUILD: "cp310-* cp311-* cp312-* cp313-* cp313t-* cp314-* cp314t-*"
CIBW_ARCHS_LINUX:   "x86_64 aarch64"
CIBW_ARCHS_MACOS:   "x86_64 arm64"
CIBW_ARCHS_WINDOWS: "AMD64"
CIBW_SKIP: "pp*"                      # PyPy: numpy C-API ufuncs are not worth it
CIBW_TEST_REQUIRES: "pytest hypothesis mpmath scipy"
CIBW_TEST_COMMAND: "pytest -q {project}/tests"
```

Free-threaded targets (`cp313t`, `cp314t`) may only be enabled once the RNG lock and
the wilcox/signrank cache lock exist — see [05-errors.md](05-errors.md#free-threaded-builds).
Until then, exclude them rather than shipping something unsafe.

The sdist must build offline from a clean checkout: `vendor/nmath/` is **committed**,
not downloaded at build time. `tools/sync_rmath.py` is a maintainer tool, never a build
step. A user behind a firewall running `pip install accudist --no-binary :all:` must
succeed.

## uv

No special handling needed — PEP 517 compliance is sufficient. Verify explicitly in CI:

```bash
uv pip install accudist
uv pip install --no-binary accudist accudist    # forces a source build
uv run --with accudist python -c "import accudist"
```

## Licensing obligations

Shipping GPL-2.0-or-later binaries means:

- `LICENSE` (GPL-2) at the wheel root, plus `vendor/nmath/COPYING`.
- Per-file R Core copyright headers preserved verbatim in `vendor/nmath/`. Do not strip
  them, and do not add accudist headers to vendored files.
- A `NOTICE` naming R Core Team as the copyright holder of the vendored sources and
  giving the exact R version.
- The corresponding source offer is satisfied by the sdist on PyPI and the public repo.
- README states the licence prominently, including that **importing accudist makes the
  importing work subject to the GPL**. Users deserve to learn that before `pip install`,
  not after legal review.

Never vendor Apache-2.0 code: it is incompatible with GPL-2.

## CI

| Workflow | Trigger | Does |
|---|---|---|
| `test.yml` | push, PR | build + `pytest` on Linux/macOS/Windows × 3.10–3.14 |
| `codegen.yml` | push, PR | `tools/regen.py --check`, `tools/check_inventory.py` |
| `wheels.yml` | tag, manual | cibuildwheel matrix → PyPI (trusted publishing) |
| `reference.yml` | manual | install R 4.5.2, regenerate goldens, open a PR on diff |

`codegen.yml` is the guard that keeps `functions.toml` authoritative. If it fails,
someone hand-edited a generated file.

## Versioning

`MAJOR.MINOR.PATCH`, plus the pinned R version in metadata and `accudist.__r_version__`.
An R bump that changes any golden value is at minimum a **MINOR** bump with every
changed value listed in `CHANGELOG.md`. Adding a sanctioned deviation is also MINOR and
is announced, never silent.
