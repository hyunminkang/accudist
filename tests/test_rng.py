from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import struct

import numpy as np
import pytest
from scipy import stats

import accudist as ad
import accudist.rmath as rmath
from accudist import _ufuncs
from accudist._platform import platform_id


DATA = Path(__file__).parent / "data"
SEED_CONTRACT = json.loads((DATA / "rng" / "seed-state.json").read_text())


def _assert_seed_contract(document):
    assert document["meta"]["r_version"] == SEED_CONTRACT["meta"]["r_version"]
    assert len(document["cases"]) == len(SEED_CONTRACT["cases"])
    for case, expected in zip(
        document["cases"], SEED_CONTRACT["cases"], strict=True
    ):
        assert {
            "function": case["function"],
            "seed": case["seed"],
            "args": case["args"],
            "final_seed": case["final_seed"],
        } == expected


def test_rng_objects_with_same_seed_reproduce_exactly():
    first = ad.RNG(42, 99)
    second = ad.RNG(42, 99)
    np.testing.assert_array_equal(first.rpois(100, 3.5), second.rpois(100, 3.5))
    assert first.get_seed() == second.get_seed()


def test_committed_self_referential_rng_vectors():
    path = DATA / platform_id() / "rng.json"
    if not path.is_file():
        raise RuntimeError(
            f"no committed standalone Rmath RNG vectors for {platform_id()}; "
            "release is blocked"
        )
    data = json.loads(path.read_text())
    assert "self-referential" in data["meta"]["oracle"]
    assert data["meta"]["r_version"] == ad.__r_version__
    assert data["meta"]["platform"] == platform_id()
    _assert_seed_contract(data)
    for case in data["cases"]:
        rng = ad.RNG(*case["seed"])
        actual = getattr(rng, case["function"])(*case["args"])
        actual_hex = [f"0x{struct.pack('>d', float(value)).hex()}" for value in actual]
        assert actual_hex == case["hex"]
        assert list(rng.get_seed()) == case["final_seed"]


def test_all_platform_rng_vectors_share_the_seed_state_contract():
    paths = tuple(DATA.glob("*/rng.json"))
    assert paths
    for path in paths:
        _assert_seed_contract(json.loads(path.read_text()))


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


def test_noncentral_rf_and_rt_preserve_r_draw_order():
    composed_f = ad.RNG(77, 91)
    manual_f = ad.RNG(77, 91)
    actual_f = composed_f.rf(8, 4.0, 6.0, ncp=1.5)
    expected_f = (manual_f.rchisq(8, 4.0, ncp=1.5) / 4.0) / (manual_f.rchisq(8, 6.0) / 6.0)
    np.testing.assert_array_equal(actual_f, expected_f)
    assert composed_f.get_seed() == manual_f.get_seed()

    composed_t = ad.RNG(77, 91)
    manual_t = ad.RNG(77, 91)
    actual_t = composed_t.rt(8, 7.0, ncp=1.5)
    expected_t = manual_t.rnorm(8, 1.5) / np.sqrt(manual_t.rchisq(8, 7.0) / 7.0)
    np.testing.assert_array_equal(actual_t, expected_t)
    assert composed_t.get_seed() == manual_t.get_seed()


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
    assert sorted(item.tobytes() for item in actual) == sorted(item.tobytes() for item in expected)


def test_fixed_seed_samplers_pass_goodness_of_fit_at_one_in_a_million():
    normal = ad.RNG(1701, 2203).rnorm(20_000)
    assert stats.kstest(normal, "norm").pvalue > 1e-6
    poisson = ad.RNG(1701, 2203).rpois(50_000, 3.5)
    observed = np.bincount(poisson.astype(int), minlength=16)[:16].astype(float)
    observed[-1] += np.count_nonzero(poisson >= 16)
    expected = np.array([ad.dpois(k, 3.5) for k in range(15)] + [ad.ppois(14, 3.5, lower_tail=False)]) * poisson.size
    assert stats.chisquare(observed, expected).pvalue > 1e-6


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
