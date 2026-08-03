"""Reproduce the scalar-overhead and array-throughput measurements."""

from timeit import repeat

import numpy as np
import scipy.stats as stats

import accudist as ad


def best(statement, globals_, number):
    return min(repeat(statement, globals=globals_, number=number, repeat=5)) / number


x = np.linspace(-8, 8, 100_000)
rows = [
    ("scalar pnorm", best("ad.pnorm(1.25)", globals(), 100_000), best("stats.norm.cdf(1.25)", globals(), 100_000)),
    ("array pnorm / element", best("ad.pnorm(x)", globals(), 100) / x.size, best("stats.norm.cdf(x)", globals(), 100) / x.size),
]
for label, accudist_time, scipy_time in rows:
    print(f"{label}: accudist={accudist_time * 1e6:.3f} us scipy={scipy_time * 1e6:.3f} us")
