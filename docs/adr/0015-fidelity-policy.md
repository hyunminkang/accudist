---
id: adr-0015
title: "ADR-0015: Bit-exact by default; clear R bugs fixed"
status: reference
decision: accepted
date: 2026-08-02
---

# ADR-0015 — Fidelity policy

## Context

R's own nmath is sometimes imprecise. Maechler's DPQ package exists precisely because
R's d/p/q have documented soft spots (`qbeta`, `pnbeta`, `ptukey` corners).

## Decision

Match R exactly by default. Where R is demonstrably wrong against a high-precision
oracle, accudist returns the correct value and records the departure in
`tests/deviations.toml`.

## Rejected

| Option | Why not |
|---|---|
| Strict fidelity, improvements only behind an opt-in flag | Was the recommendation, on the grounds that a falsifiable "agrees with R" claim is the reason to prefer accudist. The user chose to fix clear bugs by default. |
| Fidelity as a starting point, accuracy as the goal | Turns the project into a numerics research programme rather than a binding; the oracle would have to become mpmath, which has no `ptukey`/`pwilcox` reference at all. |

## Consequences

- This is in **direct tension** with ADR-0013's bit-exact default. ADR-0016's evidence
  bar plus mandatory human review is what keeps the tension from eroding the contract.
- `deviations.toml` is the *only* sanctioned way to be non-bit-exact. CI fails on any
  unlisted mismatch.
- mpmath becomes a required dev dependency — it is the oracle the evidence bar depends on.
- Agents may propose deviations but never ship them; promotion is a human edit.
