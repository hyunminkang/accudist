from concurrent.futures import ThreadPoolExecutor

import numpy as np

import accudist as ad
import accudist.rmath as rmath
from accudist import _ufuncs


def test_wilcox_cache_is_safe_across_threads():
    cases = [(5, 3, 4), (12, 5, 6), (20, 7, 8), (30, 8, 9)]
    expected = [ad.pwilcox(*case) for case in cases]
    with ThreadPoolExecutor(max_workers=8) as pool:
        actual = list(pool.map(lambda case: ad.pwilcox(*case), cases * 25))
    np.testing.assert_array_equal(actual, expected * 25)


def test_independent_rngs_are_thread_safe():
    seeds = [(index + 1, index + 101) for index in range(8)]
    expected = [ad.RNG(*seed).rgamma(10_000, 2.5) for seed in seeds]
    with ThreadPoolExecutor(max_workers=8) as pool:
        actual = list(pool.map(lambda seed: ad.RNG(*seed).rgamma(10_000, 2.5), seeds))
    for got, want in zip(actual, expected, strict=True):
        np.testing.assert_array_equal(got, want)


def test_raw_rng_ufuncs_serialize_the_entire_vector_loop():
    means = np.zeros(20_000)
    scales = np.ones(20_000)
    _ufuncs._set_seed(301, 907)
    expected = [rmath.rnorm(means, scales) for _ in range(4)]
    _ufuncs._set_seed(301, 907)
    with ThreadPoolExecutor(max_workers=4) as pool:
        actual = list(pool.map(lambda _: rmath.rnorm(means, scales), range(4)))
    assert sorted(item.tobytes() for item in actual) == sorted(
        item.tobytes() for item in expected
    )
