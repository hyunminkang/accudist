---
id: testing
title: Testing and the correctness contract
status: normative
audience: agents
updated: 2026-08-02
---

# 08 — Testing and the correctness contract

## The contract

> For every function and every input, `accudist` returns the **same 64 bits** as
> R 4.5.2, unless that input falls in a region listed in `tests/deviations.toml`.

This is falsifiable, which is the point. No other Python distribution package makes a
claim this strong, and it is only credible if the suite actually enforces it.

## Five test layers

| Layer | File | Needs R? | Asserts |
|---|---|---|---|
| 1. Golden vectors | `tests/test_golden.py` | no (pre-generated) | bit-exact equality with R |
| 2. Invariants | `tests/test_invariants.py` | no | mathematical identities |
| 3. scipy gap | `tests/test_scipy_gap.py` | no | accudist is right where scipy isn't |
| 4. Deviations | `tests/test_deviations.py` | no | gated departures behave as recorded |
| 5. Machinery | `tests/test_{errstate,rng,layering,compat}.py` | no | plumbing |

Only reference *generation* needs R. The suite itself runs offline, on any platform.

---

## Layer 1 — golden vectors

### Generation

`tools/gen_reference.R` walks `functions.toml` and, for each function, evaluates a
designed grid under R, writing JSONL to `tests/data/<name>.jsonl`:

```json
{"args": [200.0, 0.1], "lower_tail": 0, "log": 1, "hex": "0xc094ce8bf1c9e3a1"}
```

**Values are stored as raw 64-bit hex, never as decimal.** `%.17g` round-trips in
practice but hex removes the question entirely, and it makes a one-ulp diff visible in
the diff view.

The R version is recorded in a header record; the suite fails loudly if
`vendor/VENDOR.toml` and the golden files disagree about which R produced them.

### Grid design

Random sampling is the wrong tool — the failures are at the edges. Each function's grid
is the cross product of:

- **all four flag combinations** — `lower_tail` × `log`. The upper-tail log branch is
  the whole reason this package exists and is also the least-exercised code in nmath.
- **tails**: quantiles at `1e-300`, `1e-100`, `1e-15`, `0.5`, `1 - 1e-15`, and the
  far-tail arguments where scipy underflows
- **boundaries**: `0`, `1`, `±Inf`, `NaN`, and the exact support endpoints
- **domain errors**: negative `size`, `prob` outside [0,1], non-integer `df` where
  disallowed — these must return `NaN` *and* set the domain flag
- **parameter scale**: tiny (`1e-10`), moderate, huge (`1e10`) for every shape/rate/df
- **integer edges** for discrete distributions: `x`, `x ± 0.5`, `x ± 1e-9`
- **`ncp`**: `None` *and* `0.0` for every dispatching function — they take different
  code paths and must both be pinned

Aim for 200–500 points per function. The grid generator is shared, in
`tools/grids.py`, so a fix to the grid improves every function at once.

### Assertion

```python
assert struct.pack('<d', got) == struct.pack('<d', want)   # bit-exact
```

with NaN compared by bit pattern, not by `==`.

### The ulp waiver list

`tests/ulp_waivers.toml` lists functions permitted to differ from R by a bounded number
of ulps, for reasons of **floating-point environment**, not algorithm:

```toml
[[waiver]]
func = "pnbeta"
max_ulp = 2
reason = "FMA contraction differs between the R build and ours on aarch64"
platforms = ["linux-aarch64", "macos-arm64"]
```

A waiver is *not* a deviation. Waivers cover the same algorithm producing a
last-bit-different answer because of contraction or x87 excess precision. Deviations
cover accudist deliberately returning a different value.

Keep waivers scarce. Build with `-ffp-contract=off` and without `-ffast-math` first;
that removes most of the need. If a waiver's `max_ulp` needs to exceed ~4, it is not a
waiver — investigate.

---

## Layer 2 — invariants

No oracle needed, and they cover the whole input space rather than a grid.

| Invariant | Applies to |
|---|---|
| `p(q, lower=T) + p(q, lower=F) == 1` (to rtol 1e-14, in linear space) | all `p*` |
| `exp(p(q, log=T)) == p(q, log=F)` where representable | all `p*` |
| `p(q, log=T) <= 0` | all `p*` |
| `p` is monotone non-decreasing in `q` | all `p*` |
| `q(p(x)) == x` for continuous distributions (rtol 1e-9) | all `q*` |
| `q(p, lower=T) == q(1-p, lower=F)` | all `q*` |
| `d >= 0`; `d(x, log=T) == log(d(x))` | all `d*` |
| `sum(d(0..N)) -> 1` for discrete with finite support | discrete `d*` |
| `p(q) == sum(d(0..q))` for discrete | discrete |
| NaN in → NaN out | all |

Drive these with Hypothesis over sensible parameter ranges, with a fixed seed and a
recorded example database, so failures reproduce.

---

## Layer 3 — the scipy gap suite

Marked `@pytest.mark.scipy_gap`. Pins the reason the project exists:

```python
@pytest.mark.scipy_gap
def test_poisson_upper_log_tail():
    got = ad.ppois(200, 0.1, lower_tail=False, log=True)
    assert got == pytest.approx(-1331.4544, abs=1e-3)
    assert np.isneginf(scipy.stats.poisson.logsf(200, 0.1))   # documents the gap
```

The scipy assertion is intentional. When scipy eventually fixes one of these, the test
fails and tells you to move the case into the "scipy is now fine" table in
[appendix/scipy-gap-evidence.md](appendix/scipy-gap-evidence.md) — which is exactly the
maintenance signal you want. Mark those with `xfail(strict=False)` once observed.

Seed this suite from the measured table in the appendix.

---

## The deviation review process

nmath is 25+ years old and exercised by every R user on earth. **The expected number of
deviations is approximately zero.** Treat any apparent R bug as a wrapper bug until the
evidence says otherwise — it almost always is.

Accordingly the rule has two parts: a **technical bar** an agent can clear on its own,
and a **human review** an agent cannot.

### The technical bar — mpmath evidence

A candidate needs a ≥50-digit `mpmath` (or `Rmpfr`, where mpmath has no equivalent)
reference showing R's error exceeds **100 ulp** or loses more than **3 significant
digits**.

This threshold is a *screening filter*, not a correctness boundary. Its job is to decide
what deserves a human's attention. Below it, change nothing and record nothing.

### The human review — mandatory, not automatable

> **An agent may never ship a deviation. An agent may only propose one.**

Mechanically:

| file | who writes it | effect on the build |
|---|---|---|
| `tests/deviations.pending.toml` | agents | **none** — never read by the runtime or the suite |
| `tests/deviations.toml` | a human, after review | the deviation takes effect |

An agent that finds a candidate writes it to the **pending** file and **leaves the
implementation matching R**. It does not change the algorithm, does not touch golden
vectors, and does not weaken a test. The bit-exact test for that region continues to
pass, because nothing changed.

Promotion from pending to active is a human edit. Each active entry requires
`reviewed_by` and `reviewed_date`; CI fails on any entry lacking them, which is what
makes "manually reviewed" an enforced property rather than an intention.

```toml
# tests/deviations.toml — entries here are ACTIVE
[[deviation]]
func     = "qbeta"
region   = "shape1 < 1e-3 and shape2 > 1e5"
r_value  = "0x3f847ae147ae147b"
ours     = "0x3f847ae147ae1480"
oracle   = "mpmath, 50 digits"
oracle_value = "0.0100000000000000002081668171172..."
ulp_error_r  = 4.2e6
replacement  = "DPQ::qbetaAppr"        # provenance, or "none — hand-derived"
upstream     = "https://bugs.r-project.org/show_bug.cgi?id=NNNNN"   # optional
reviewed_by  = "hyun.kang"             # REQUIRED — CI fails without it
reviewed_date = "2026-08-02"           # REQUIRED
```

### What the reviewer is deciding

The pending entry must state, honestly, enough for a human to judge:

- the reproduction **in plain R**, with no accudist involved
- the high-precision reference and the measured error
- the proposed replacement and **its provenance** — R-devel, a published method, or
  DPQ. If the agent has nothing vetted, it must say `replacement = "none — hand-derived"`
  rather than presenting invented numerics as established. An unvetted replacement is
  not disqualifying; concealing that it is unvetted is.
- whether it has been reported upstream. Recommended, tracked in the entry, **not
  blocking** — R Core's response time should not gate accudist's correctness.

### Enforcement

Everything outside an active region stays bit-exact and CI fails on any unlisted
mismatch. `tests/test_deviations.py` additionally asserts that inside each active region
the accudist value matches the recorded `oracle_value`, so a deviation cannot silently
rot into a different wrong answer.

If the bar is not met, or review has not happened, **match R**. A known, documented R
quirk is better than an undocumented accudist quirk.

Candidate regions are catalogued in
[appendix/known-r-limitations.md](appendix/known-r-limitations.md) — as *candidates*,
not approvals.

---

## Running

```bash
pytest -q                     # everything, offline
pytest -q -m scipy_gap        # just the motivating cases
pytest -q -m "not slow"       # skip the large wilcox/signrank grids
Rscript tools/gen_reference.R # regenerate goldens (needs R 4.5.2)
```

CI runs the full suite on every wheel target. The golden vectors are platform
independent by construction; if one fails on a single platform, that is a real
floating-point-environment finding and belongs in the waiver discussion, not a skip.
