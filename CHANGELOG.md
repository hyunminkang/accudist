# Changelog

## 0.1.0 (unreleased)

First release. Wraps R 4.5.2's `nmath` library as NumPy ufuncs.

- All 106 scalar functions from `Rmath.h` with a public R-style wrapper:
  d/p/q/r for 21 distribution families (including the non-central beta, chi-squared,
  F and t, Tukey's studentized range, Wilcoxon rank-sum and signed-rank), the
  gamma/beta/Bessel special functions and R's numerically careful utilities.
- `lower_tail=False` and `log=True` everywhere, computed by R's direct algorithms.
- `ncp=None` / `prob`-or-`mu` / `rate`-or-`scale` dispatch reproducing R's semantics.
- `errstate` for nmath's domain/range/convergence conditions; allocation failures
  raise `MemoryError` instead of exiting the process, and nothing is ever printed.
- `RNG` objects with independent, thread-safe Marsaglia-MultiCarry streams (not
  compatible with R's `set.seed()`), plus `rmultinom`.
- `accudist.compat`: a deliberately partial `scipy.stats`-shaped shim
  (`pmf/pdf, cdf, sf, ppf, isf, rvs` and their log variants).
- Reference tests against R 4.5.2 on ~21 000 designed grid points at eight
  significant digits.
