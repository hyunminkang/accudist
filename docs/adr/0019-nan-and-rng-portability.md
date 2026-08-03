---
status: accepted
date: 2026-08-03
---

# Treat NaN encodings as semantic and RNG draws as platform-specific

Official R binaries and standalone Rmath builds can differ only in a NaN's sign or
payload, and compiler math libraries can move finite RNG transforms by a few ulps.
Oracle equality therefore ignores NaN sign and payload while retaining exact bits for
finite values, signed zero, and infinities. RNG draw vectors are selected by supported
OS/architecture, while their seed-state transitions remain exact. This narrows the
portability claims in ADR-0013 and the RNG specification without introducing a general
floating-point tolerance.

## Consequences

- NaN-producing regressions remain visible when one side is not NaN.
- Deterministic distribution results remain bit-exact except for reviewed ulp waivers.
- RNG regressions remain bit-exact against a committed vector generated on that
  platform; cross-platform equality of transformed draws is no longer promised.
