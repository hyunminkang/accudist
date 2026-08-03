from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest

import accudist as ad


def test_rng_objects_with_same_seed_reproduce_exactly():
    first = ad.RNG(42, 99)
    second = ad.RNG(42, 99)
    np.testing.assert_array_equal(first.rpois(100, 3.5), second.rpois(100, 3.5))
    assert first.get_seed() == second.get_seed()


def test_default_rng_seed_controls_module_functions():
    ad.set_seed(1234, 5678)
    first = ad.rnorm(12)
    final_seed = ad.get_seed()
    ad.set_seed(1234, 5678)
    np.testing.assert_array_equal(ad.rnorm(12), first)
    assert ad.get_seed() == final_seed


def test_rng_parameter_recycling_and_length_guard():
    rng = ad.RNG(1234, 5678)
    result = rng.rnorm(5, mean=[0.0, 10.0], sd=1.0)
    assert result.shape == (5,)
    with pytest.raises(ValueError, match="longer than the draw count"):
        rng.rnorm(2, mean=[0.0, 1.0, 2.0])


def test_noncentral_rbeta_preserves_r_draw_order():
    composed = ad.RNG(77, 91)
    manual = ad.RNG(77, 91)
    actual = composed.rbeta(8, 2.0, 3.0, ncp=1.5)
    x = manual.rchisq(8, 4.0, ncp=1.5)
    expected = x / (x + manual.rchisq(8, 6.0))
    np.testing.assert_array_equal(actual, expected)
    assert composed.get_seed() == manual.get_seed()


def test_independent_rngs_are_thread_safe():
    seeds = [(index + 1, index + 101) for index in range(8)]
    expected = [ad.RNG(*seed).rgamma(1000, 2.5) for seed in seeds]
    with ThreadPoolExecutor(max_workers=8) as pool:
        actual = list(pool.map(lambda seed: ad.RNG(*seed).rgamma(1000, 2.5), seeds))
    for got, want in zip(actual, expected, strict=True):
        np.testing.assert_array_equal(got, want)


def test_every_random_function_docstring_has_stream_caveat():
    for name in ad.__all__:
        if name.startswith("r") and callable(getattr(ad, name)):
            assert "does not reproduce R's set.seed" in getattr(ad, name).__doc__


def test_rmultinom_is_deterministic_and_validates_probability_sum():
    first = ad.RNG(81, 92)
    second = ad.RNG(81, 92)
    got = first.rmultinom(20, 12, [0.2, 0.3, 0.5])
    np.testing.assert_array_equal(got, second.rmultinom(20, 12, [0.2, 0.3, 0.5]))
    assert got.shape == (20, 3)
    np.testing.assert_array_equal(got.sum(axis=1), np.full(20, 12))
    with pytest.raises(ValueError, match="sum to 1"):
        ad.rmultinom(1, 5, [0.2, 0.2])
