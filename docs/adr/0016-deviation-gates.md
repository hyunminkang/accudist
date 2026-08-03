---
id: adr-0016
title: "ADR-0016: Deviations need mpmath evidence plus human review"
status: reference
decision: accepted
date: 2026-08-02
revised: 2026-08-02
---

# ADR-0016 — The deviation bar

## Context

ADR-0015 permits fixing clear R bugs. Without a governing rule, every agent applies its
own threshold and the bit-exact suite erodes into a tolerance suite.

Two facts shape the rule:

1. **nmath is 25+ years old and exercised by every R user.** Real bugs in it are rare.
   The expected number of deviations over accudist's lifetime is approximately zero, and
   any given discrepancy is overwhelmingly more likely to be a wrapper bug.
2. **The dangerous failure is not a missed R bug — it is an agent inventing numerics**
   that are wrong in a region nobody tested, shipped under a claim of being "more
   accurate than R".

## Decision

Two parts.

**Technical bar — an agent can clear this alone.** A ≥50-digit mpmath/Rmpfr reference
showing R's error exceeds 100 ulp or loses >3 significant digits. This is a screening
filter for what deserves human attention, not a correctness boundary.

**Human review — an agent cannot clear this.** An agent may *propose* a deviation, never
ship one. Candidates go to `tests/deviations.pending.toml`, which nothing reads;
promotion to `tests/deviations.toml` is a human edit, and each active entry requires
`reviewed_by` and `reviewed_date`. CI fails without them.

An agent that finds a candidate **leaves the implementation matching R**: it does not
change the algorithm, touch golden vectors, or weaken a test.

Upstream reporting is recommended and recorded, but **not blocking**.
Replacement-algorithm provenance must be *disclosed* (`replacement = "none —
hand-derived"` when unvetted) but is not *required* — the reviewer weighs it.

## Rejected

| Option | Why not |
|---|---|
| Maintainer judgment, documented after the fact | Gives an agent no operable rule — precisely the failure mode these docs exist to prevent. |
| **Four blocking gates** (mpmath + vetted replacement + upstream report + record) | The original decision; superseded before implementation began — see Revision below. |

## Revision — 2026-08-02

The first version of this ADR required four *blocking* gates. It was revised the same
day, before any implementation, on the maintainer's judgement that R bugs are rare
enough that mpmath evidence is a sufficient technical bar, and that deviations warrant
manual review instead.

What changed:

- **Gate 2 (vetted replacement) — blocking → disclosed.** The original concern was an
  agent hand-rolling numerics that are wrong in a different region. Human review
  addresses that concern *better*: a reviewer can weigh an unvetted replacement on its
  merits, where a hard rule would have blocked a genuinely correct fix for want of a
  citation. Disclosure stays mandatory; concealment is the real failure.
- **Gate 3 (upstream report) — blocking → recommended.** Gating accudist's correctness
  on R Core's response time helped nobody. Still encouraged, still recorded.
- **Gate 1 (mpmath evidence) and Gate 4 (recorded) — retained unchanged.**
- **Added: mandatory human sign-off**, enforced by required `reviewed_by` /
  `reviewed_date` fields and the pending/active file split.

Net effect: the bar on *evidence* is unchanged, the bar on *process* is lower, and the
bar on *autonomy* is higher. An agent could previously have shipped a deviation by
satisfying four mechanical checks; now it cannot ship one at all.

## Consequences

- "We fixed R" is a human decision with an audit trail, not an agent's judgement call.
- The pending file means a candidate is never lost, and never silently active.
- `test_deviations.py` asserts the accudist value matches the recorded oracle value, so
  a deviation cannot rot into a different wrong answer.
- If the bar is not met, or review has not happened, **match R**.
