# Benchmarks

These measurements compare wrapper overhead and array throughput; they are not a
claim that every distribution has the same profile. Run `python benchmarks/benchmark.py`
from an installed checkout to reproduce them.

Platform recorded on 2026-08-02: macOS 26.3 arm64, CPython 3.11, NumPy 1.26.4,
scipy 1.17.1. Values are the best of five runs.

| operation | accudist | scipy |
|---|---:|---:|
| scalar `pnorm(1.25)` | 1.439 µs | 20.957 µs |
| 100k-element `pnorm`, per element | 0.018 µs | 0.016 µs |

Scalar calls include accudist's thread-local error capture and policy check. That
wrapper costs roughly 1.4 microseconds on this machine; array calls amortize it over
the whole ufunc loop. scipy's scalar number includes its substantially broader
distribution-object machinery, so it is context rather than a like-for-like wrapper
microbenchmark.
