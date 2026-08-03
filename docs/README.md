---
id: index
title: accudist design documentation — index
status: normative
audience: agents
updated: 2026-08-02
---

# accudist design docs — index

Entry point is [../AGENTS.md](../AGENTS.md). Read that first; it routes you here.

Every document declares `status:` in its front matter:

| status | meaning | agent behaviour |
|---|---|---|
| `normative` | an instruction | implement it; deviations need an ADR |
| `reference` | background, evidence, rationale | read for context; **never implement from it** |

---

## Normative specifications

| # | Document | Covers | Needed for |
|---|---|---|---|
| 01 | [01-architecture.md](01-architecture.md) | layer diagram, module boundaries, what may import what | all |
| 02 | [02-vendoring.md](02-vendoring.md) | pulling `src/nmath` from the R tarball, the patch set, R version bumps | M1 |
| 03 | [03-codegen-spec.md](03-codegen-spec.md) | `functions.toml` schema, generator contract, emitted artifacts | M1, M2 |
| 04 | [04-api-reference.md](04-api-reference.md) | naming rules, signatures, dispatch, argument-order hazards | M2+ |
| 05 | [05-errors.md](05-errors.md) | `errstate`, thread-local flags, removing `exit(1)`, cache lifecycles | M1 |
| 06 | [06-rng.md](06-rng.md) | `r*` functions, `RNG` objects, the global lock, R-incompatibility | M4 |
| 07 | [07-compat-layer.md](07-compat-layer.md) | `accudist.compat`, `loc`/`scale` mapping, what is deliberately absent | M5 |
| 08 | [08-testing.md](08-testing.md) | golden vectors, bit-exactness, the deviation review process, grids | M1+ |
| 09 | [09-build-release.md](09-build-release.md) | repo scaffold, meson, wheels, CI, PyPI | M1, M6 |
| 10 | [10-milestones.md](10-milestones.md) | M1–M6 with acceptance criteria | all |

## Machine-readable specification

| File | Role |
|---|---|
| [functions.toml](functions.toml) | **Canonical inventory.** 106 generated functions + 4 bespoke + 5 RNG primitives + 20 documented exclusions. Verified against R 4.5.2's `Rmath.h` and R's own closures. Copy verbatim into the implementation repo. |
| [../tools/gen_functions_toml.py](../tools/gen_functions_toml.py) | Regenerates the above. Lives here, not in the implementation repo. |

## Reference material — do not implement from these

| Document | Contains |
|---|---|
| [adr/](adr/) | Architecture Decision Records, incl. the options that were **rejected** and why. Consult before proposing a change to a settled decision. |
| [appendix/scipy-gap-evidence.md](appendix/scipy-gap-evidence.md) | Measured scipy-vs-R comparison that motivates the project |
| [appendix/rmath-inventory.md](appendix/rmath-inventory.md) | Raw symbol inventory of `Rmath.h` with implementation status |
| [appendix/known-r-limitations.md](appendix/known-r-limitations.md) | Places R itself is weak; candidate deviations |

---

## Decision summary

Every one of these is settled and has an ADR. Do not relitigate without new information.

| Area | Decision | ADR |
|---|---|---|
| Code license | GPL-2.0-or-later | [0001](adr/0001-license.md) |
| Docs license | CC-BY-4.0 | [0001](adr/0001-license.md) |
| Repo topology | docs here, code in sibling `../accudist` | [0002](adr/0002-repo-topology.md) |
| C source | fresh `src/nmath` from R 4.5.2 tarball + sync script | [0003](adr/0003-c-source-vintage.md) |
| Binding | code-generated NumPy ufuncs in C | [0004](adr/0004-binding-technology.md) |
| Build backend | meson-python | [0005](adr/0005-build-backend.md) |
| API surface | R-flat core + partial `accudist.compat` | [0006](adr/0006-api-surface.md) |
| Signatures | mirror R; `lambda_`; `log=` everywhere, strict | [0007](adr/0007-signature-conventions.md) |
| Non-central | `ncp=None` sentinel dispatch | [0008](adr/0008-noncentral-dispatch.md) |
| Errors | `errstate` + thread-local flags | [0009](adr/0009-error-handling.md) |
| RNG | included, Marsaglia-MultiCarry, not R-reproducible | [0010](adr/0010-rng-inclusion.md) |
| RNG state | globals + `RNG` objects swapping under a lock | [0011](adr/0011-rng-state-model.md) |
| Phasing | by machinery, not by distribution | [0012](adr/0012-phasing.md) |
| Test oracle | committed golden hex from R, bit-exact default | [0013](adr/0013-test-oracle.md) |
| Special-fn naming | Rmath C names, not R names | [0014](adr/0014-special-function-naming.md) |
| Fidelity | bit-exact default; gated deviations | [0015](adr/0015-fidelity-policy.md) |
| Deviation bar | mpmath evidence + mandatory human review | [0016](adr/0016-deviation-gates.md) |
| Wheels | cibuildwheel 3.10–3.14 incl. free-threaded | [0017](adr/0017-release-matrix.md) |
| Doc structure | router + numbered specs + adr/ + appendix/ | [0018](adr/0018-doc-structure.md) |
