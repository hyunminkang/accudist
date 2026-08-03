---
id: adr-0001
title: "ADR-0001: GPL-2.0-or-later for code, CC-BY-4.0 for docs"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0001 — Licensing

## Context

R's `src/nmath` is GPL-2-or-later (`Rmath.h` itself is LGPL-2.1+, but `bd0.c`,
`mlutils.c` and essentially every other `.c` file is GPL-2+). A Python extension that
statically links these sources is a derivative work. The design repo's original
`LICENSE` was Apache-2.0, which is **incompatible with GPL-2**.

## Decision

- Implementation repo: **GPL-2.0-or-later** (SPDX `GPL-2.0-or-later`).
- Design repo: **CC-BY-4.0** — it contains prose and a TOML inventory, no GPL code.
- The README states plainly that importing accudist subjects the importing work to
  the GPL.

## Rejected

| Option | Why not |
|---|---|
| Clean-room reimplementation under BSD/MIT | 10–50× the effort, and it forfeits "bit-identical to R" as a testable guarantee — the entire product claim. |
| Split GPL core + permissive API package | Widely understood to still be GPL in effect for the combined work. Buys optics, not freedom. |
| ctypes over a system `libRmath` | Kills `pip install accudist`; users would need R installed. Destroys the wheel story. |
| **GPL-3.0-or-later** | Strictly narrower than what nmath grants: downstream loses the v2-or-v3 choice. Incompatible with GPL-2-only code. Its distinctive terms (patent grant, anti-tivoization, Apache compat) buy nothing for a numerical library whose only deps are nmath (GPL) and NumPy (BSD). Also anomalous next to R and CRAN, which ship `GPL-2 | GPL-3`. |

## Consequences

- Proprietary/commercial adoption is constrained — the same constraint rpy2 users
  already accept. This is a real cost, accepted knowingly.
- Apache-2.0 code can never be vendored.
- Per-file R Core copyright headers must be preserved verbatim; `NOTICE` names R Core
  Team and the exact R version.
