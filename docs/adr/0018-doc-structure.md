---
id: adr-0018
title: "ADR-0018: Router + numbered specs + ADRs + appendix"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0018 — Documentation structure

## Context

These documents are agent-facing build instructions. The main failure modes are agents
implementing from background material, burning context on irrelevant sections, and
relitigating settled decisions.

## Decision

`AGENTS.md` is a short normative router: invariants, hard rules, and a task→document
table. Every `docs/` file carries YAML front matter with `status: normative|reference`
and a stable `id`. ADRs record the rejected options. `functions.toml` stays the single
machine-readable source of truth; documents point at it and never duplicate it.

## Rejected

| Option | Why not |
|---|---|
| Diátaxis four-quadrant | Organized around *learning a finished product*, not *building one*. An agent asked to implement M2 has no obvious entry point, and acceptance criteria have no home. |
| Minimal: AGENTS.md + 3 large docs | Each file grows to thousands of lines; agents burn context on irrelevant sections and targeted routing becomes impossible. |
| One self-contained AGENTS.md | ~4000+ lines at this scope; blows the context budget on every task and causes constant conflicts with parallel agents. |

## Consequences

- Agents can be pointed at exactly one document for a task.
- `status:` front matter is what stops background material being implemented.
- ADRs must record rejected options, not just decisions — that is what prevents
  re-derivation.
