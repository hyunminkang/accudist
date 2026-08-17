# Benchmarks

The benchmark measures wrapper overhead and array throughput. It is not a claim
that every distribution has the same performance profile.

Run the checked-in benchmark from an installed repository checkout:

```console
python benchmarks/benchmark.py
```

## Recorded result

Platform recorded on 2026-08-02: macOS 26.3 arm64, CPython 3.11, NumPy 1.26.4,
SciPy 1.17.1. Values are the best of five runs.

| Operation | accudist | SciPy |
|---|---:|---:|
| Scalar `pnorm(1.25)` | 1.439 µs | 20.957 µs |
| 100k-element `pnorm`, per element | 0.018 µs | 0.016 µs |

Scalar calls include accudist's thread-local error capture and policy check. Array
calls amortize that wrapper over the ufunc loop. SciPy's scalar result includes its
broader distribution-object machinery, so this is context rather than a
like-for-like wrapper microbenchmark.

The source benchmark notes remain available in the
[repository](https://github.com/hyunminkang/accudist/tree/HEAD/benchmarks).
