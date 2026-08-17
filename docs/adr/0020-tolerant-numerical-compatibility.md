---
status: accepted
date: 2026-08-15
---

# Use tolerant numerical compatibility

Bit-exact agreement with an official R binary is not a compatibility requirement.
The vendored R nmath algorithms can produce slightly different finite results when
compiled with a different compiler or math library, most visibly on Windows.

Deterministic reference tests compare finite results with a package-wide relative
tolerance of `1e-10` and an absolute tolerance of zero. This covers the measured
Windows differences while retaining sensitivity for results close to zero. NaNs
compare semantically, and unmatched infinities continue to fail.

RNG tests require reproducibility for equal seeds within one build and retain
statistical goodness-of-fit checks. They do not pin exact draws or internal seed-state
transitions across versions, platforms, or generator implementations.

This decision supersedes the bit-exact deterministic and cross-build RNG consequences
recorded in ADR-0019.
