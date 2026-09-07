"""Random generation: reproducibility, stream independence, thread safety, GoF."""

import threading

import numpy as np
import pytest

import accudist as ad


def test_default_seed_matches_rmath_defaults():
    ad.set_seed(1234, 5678)
    assert ad.get_seed() == (1234, 5678)
    a = ad.runif(5)
    ad.set_seed()
    b = ad.runif(5)
    np.testing.assert_array_equal(a, b)
    assert a.dtype == np.float64 and a.shape == (5,)
    assert np.all((a >= 0) & (a < 1))


def test_rng_objects_are_independent_and_reproducible():
    r1, r2, r3 = ad.RNG.from_r_seed(42), ad.RNG.from_r_seed(42), ad.RNG.from_r_seed(7)
    x1, x2, x3 = r1.rnorm(1000), r2.rnorm(1000), r3.rnorm(1000)
    np.testing.assert_array_equal(x1, x2)
    assert not np.array_equal(x1, x3)
    assert abs(np.corrcoef(x1, x3)[0, 1]) < 0.1
    assert r1.get_seed() == r2.get_seed() != ad.RNG.from_r_seed(42).get_seed()


def test_small_raw_seeds_are_correlated_which_is_why_set_r_seed_exists():
    """Marsaglia-MultiCarry mixes small raw seeds badly; R scrambles them and so do we."""
    raw = np.corrcoef(ad.RNG(1, 2).rnorm(1000), ad.RNG(3, 4).rnorm(1000))[0, 1]
    scrambled = np.corrcoef(ad.RNG.from_r_seed(1).rnorm(1000), ad.RNG.from_r_seed(3).rnorm(1000))[0, 1]
    assert abs(raw) > 0.1 > abs(scrambled)


def test_reproduces_r_under_marsaglia_multicarry():
    """R 4.5.2: RNGkind("Marsaglia-Multicarry", "Inversion", "Rejection"); set.seed(42); ..."""
    assert ad.RNG.from_r_seed(42).get_seed() == (-2133391687 % 2**32, 507561766)  # R's .Random.seed[2:3]
    assert ad.RNG.from_r_seed(-1).get_seed() == (1342586034, -1564105589 % 2**32)
    assert ad.RNG.from_r_seed(0).get_seed() == (-835792825 % 2**32, 1280795612)
    rng = ad.RNG.from_r_seed(42)
    np.testing.assert_allclose(rng.runif(4), [0.32313144959582274, 0.44243435245995266, 0.3247694876801151, 0.60022914772858582], rtol=1e-15)
    np.testing.assert_allclose(rng.rnorm(3), [0.54253862925836582, 0.30455755805851131, 0.019091981400769897], rtol=1e-13)
    np.testing.assert_array_equal(rng.rpois(4, 4), [10, 8, 4, 3])
    np.testing.assert_array_equal(rng.rbinom(4, 10, 0.3), [1, 2, 3, 4])
    np.testing.assert_allclose(rng.rgamma(3, 2), [1.7878281673559302, 8.5680858921598571, 3.5590071182721408], rtol=1e-12)
    np.testing.assert_allclose(rng.rexp(2), [0.6518754897759933, 0.093069507197175161], rtol=1e-13)
    np.testing.assert_allclose(rng.rbeta(2, 2, 3), [0.45928230639732132, 0.38749193809291088], rtol=1e-12)
    np.testing.assert_allclose(rng.rt(2, 5), [-0.22923533798714932, 1.4940418134642268], rtol=1e-12)
    np.testing.assert_allclose(rng.rchisq(2, 3, ncp=1), [2.2046634921859898, 5.5834980167659882], rtol=1e-12)
    np.testing.assert_array_equal(rng.rhyper(3, 10, 7, 8), [6, 4, 3])
    np.testing.assert_array_equal(rng.rwilcox(3, 4, 6), [7, 11, 15])
    np.testing.assert_array_equal(rng.rsignrank(3, 10), [18, 29, 25])
    ad.set_r_seed(42)
    np.testing.assert_allclose(ad.runif(1), [0.32313144959582274], rtol=1e-15)


def test_module_functions_do_not_disturb_rng_objects():
    rng = ad.RNG(1, 2)
    first = rng.rpois(3, 4.0)
    ad.rpois(100, 4.0)  # default stream
    rng.set_seed(1, 2)
    np.testing.assert_array_equal(rng.rpois(3, 4.0), first)


def test_recycling_follows_r():
    ad.set_seed(1, 1)
    x = ad.rnorm(4, mean=np.array([0.0, 1000.0]), sd=1e-6)
    assert np.allclose(x, [0.0, 1000.0, 0.0, 1000.0], atol=1e-4)
    with pytest.raises(ValueError, match="longer than n"):
        ad.rnorm(2, mean=[0.0, 1.0, 2.0])
    assert ad.rnorm(0).shape == (0,)
    with pytest.raises(TypeError):
        ad.rnorm(2.5)
    with pytest.raises(ValueError):
        ad.rnorm(-1)


def test_discrete_draws_are_integral_doubles():
    ad.set_seed(3, 4)
    for x in (ad.rpois(50, 3.0), ad.rbinom(50, 10, 0.3), ad.rgeom(50, 0.2), ad.rhyper(50, 10, 7, 8),
              ad.rnbinom(50, 3, 0.4), ad.rnbinom(50, 3, mu=4.0), ad.rwilcox(50, 4, 6), ad.rsignrank(50, 10)):
        assert x.dtype == np.float64
        np.testing.assert_array_equal(x, np.round(x))


def test_dispatching_draws():
    rng = ad.RNG(5, 6)
    assert rng.rchisq(3, 4.0, ncp=2.0).shape == (3,)
    assert rng.rbeta(3, 2.0, 3.0, ncp=1.0).shape == (3,)
    assert rng.rf(3, 2.0, 3.0, ncp=1.0).shape == (3,)
    assert rng.rt(3, 5.0, ncp=1.0).shape == (3,)
    assert rng.rgamma(3, 2.0, rate=2.0).shape == (3,)
    assert rng.rexp(3, rate=2.0).shape == (3,)
    with pytest.raises(TypeError):
        rng.rnbinom(3, 2.0, 0.5, 4.0)


def test_composed_noncentral_draws_consume_the_documented_streams():
    """rt(n, df, ncp) == rnorm(n, ncp) / sqrt(rchisq(n, df) / df), in that order."""
    a, b = ad.RNG(11, 12), ad.RNG(11, 12)
    got = a.rt(5, 4.0, ncp=1.5)
    z = b.rnorm(5, 1.5)
    c = b.rchisq(5, 4.0)
    np.testing.assert_allclose(got, z / np.sqrt(c / 4.0))
    assert a.get_seed() == b.get_seed()

    a, b = ad.RNG(11, 12), ad.RNG(11, 12)
    got = a.rbeta(5, 2.0, 3.0, ncp=1.0)
    x = b.rchisq(5, 4.0, ncp=1.0)
    y = b.rchisq(5, 6.0)
    np.testing.assert_allclose(got, x / (x + y))

    a, b = ad.RNG(11, 12), ad.RNG(11, 12)
    got = a.rf(5, 2.0, 3.0, ncp=1.0)
    x = b.rchisq(5, 2.0, ncp=1.0)
    y = b.rchisq(5, 3.0)
    np.testing.assert_allclose(got, (x / 2.0) / (y / 3.0))


def test_rmultinom():
    rng = ad.RNG(1, 2)
    r = rng.rmultinom(4, 10, [0.2, 0.3, 0.5])
    assert r.shape == (4, 3) and r.dtype.kind == "i"
    assert np.all(r.sum(axis=1) == 10)
    with pytest.raises(ValueError, match="probability sum"):
        rng.rmultinom(1, 10, [0.5, 0.6])
    assert ad.rmultinom(0, 10, [1.0]).shape == (0, 1)


def test_primitives():
    rng = ad.RNG(9, 9)
    u = rng.unif_rand(1000)
    assert np.all((u >= 0) & (u < 1))
    assert abs(rng.norm_rand(4000).mean()) < 0.1
    assert abs(rng.exp_rand(4000).mean() - 1.0) < 0.1
    assert ad.unif_rand(3).shape == (3,)


def test_bad_seed_words():
    with pytest.raises(ValueError):
        ad.RNG(-1, 0)
    with pytest.raises(ValueError):
        ad.RNG(2**32, 0)


@pytest.mark.slow
def test_threads_reproduce_single_threaded_streams():
    seeds = [(i + 1, 1000 + i) for i in range(8)]
    expected = [ad.RNG(*s).rgamma(20000, 2.5, scale=1.5) for s in seeds]
    results = [None] * 8

    def worker(i):
        rng = ad.RNG(*seeds[i])
        chunks = [rng.rgamma(5000, 2.5, scale=1.5) for _ in range(4)]
        results[i] = np.concatenate(chunks)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for got, want in zip(results, expected):
        np.testing.assert_array_equal(got, want)


def ks_statistic(sample, cdf):
    x = np.sort(sample)
    n = len(x)
    f = cdf(x)
    return max(np.max(np.arange(1, n + 1) / n - f), np.max(f - np.arange(0, n) / n))


@pytest.mark.parametrize(
    "draw, cdf",
    [
        (lambda r, n: r.rnorm(n, 1.0, 2.0), lambda x: ad.pnorm(x, 1.0, 2.0)),
        (lambda r, n: r.rgamma(n, 2.5, scale=1.5), lambda x: ad.pgamma(x, 2.5, scale=1.5)),
        (lambda r, n: r.rbeta(n, 0.5, 2.0), lambda x: ad.pbeta(x, 0.5, 2.0)),
        (lambda r, n: r.rt(n, 3.0), lambda x: ad.pt(x, 3.0)),
        (lambda r, n: r.rchisq(n, 4.0, ncp=2.0), lambda x: ad.pchisq(x, 4.0, ncp=2.0)),
        (lambda r, n: r.rweibull(n, 1.5, 2.0), lambda x: ad.pweibull(x, 1.5, 2.0)),
        (lambda r, n: r.rlnorm(n, 0.5, 0.8), lambda x: ad.plnorm(x, 0.5, 0.8)),
        (lambda r, n: r.rcauchy(n, 0.0, 1.0), lambda x: ad.pcauchy(x, 0.0, 1.0)),
        (lambda r, n: r.rlogis(n, 0.0, 1.0), lambda x: ad.plogis(x, 0.0, 1.0)),
        (lambda r, n: r.rexp(n, 3.0), lambda x: ad.pexp(x, 3.0)),
        (lambda r, n: r.runif(n, -1.0, 2.0), lambda x: ad.punif(x, -1.0, 2.0)),
        (lambda r, n: r.rf(n, 5.0, 7.0), lambda x: ad.pf(x, 5.0, 7.0)),
    ],
)
def test_continuous_goodness_of_fit(draw, cdf):
    n = 20000
    d = ks_statistic(draw(ad.RNG(2024, 7), n), cdf)
    # Kolmogorov critical value at alpha = 1e-6 is ~2.63/sqrt(n); fixed seed, so no flakiness
    assert d < 2.7 / np.sqrt(n)


@pytest.mark.parametrize(
    "draw, pmf, support",
    [
        (lambda r, n: r.rpois(n, 3.0), lambda k: ad.dpois(k, 3.0), np.arange(0, 15)),
        (lambda r, n: r.rbinom(n, 12, 0.3), lambda k: ad.dbinom(k, 12, 0.3), np.arange(0, 13)),
        (lambda r, n: r.rgeom(n, 0.3), lambda k: ad.dgeom(k, 0.3), np.arange(0, 15)),
        (lambda r, n: r.rnbinom(n, 3.0, 0.4), lambda k: ad.dnbinom(k, 3.0, 0.4), np.arange(0, 20)),
        (lambda r, n: r.rhyper(n, 10, 7, 8), lambda k: ad.dhyper(k, 10, 7, 8), np.arange(1, 9)),
        (lambda r, n: r.rwilcox(n, 4, 6), lambda k: ad.dwilcox(k, 4, 6), np.arange(0, 25)),
        (lambda r, n: r.rsignrank(n, 8), lambda k: ad.dsignrank(k, 8), np.arange(0, 37)),
    ],
)
def test_discrete_goodness_of_fit(draw, pmf, support):
    n = 50000
    x = draw(ad.RNG(99, 2024), n)
    observed = np.array([np.sum(x == k) for k in support])
    observed = np.append(observed, n - observed.sum())  # tail bucket
    p = pmf(support)
    p = np.append(p, max(1.0 - p.sum(), 0.0))
    keep = p * n > 5
    chi2 = np.sum((observed[keep] - n * p[keep]) ** 2 / (n * p[keep]))
    dof = keep.sum() - 1
    # chi-square critical value at alpha = 1e-6
    assert chi2 < ad.qchisq(1e-6, dof, lower_tail=False)
