"""Bespoke wrappers and the mpmath-checked utilities that have no R-level twin."""

import numpy as np
import pytest

import accudist as ad

mpmath = pytest.importorskip("mpmath")
mpmath.mp.dps = 50


def test_pnorm_both():
    x = np.array([-40.0, -3.0, 0.0, 1.5, 40.0])
    lo, up = ad.pnorm_both(x)
    np.testing.assert_array_equal(lo, ad.pnorm(x))
    np.testing.assert_array_equal(up, ad.pnorm(x, lower_tail=False))
    llo, lup = ad.pnorm_both(x, log=True)
    np.testing.assert_array_equal(llo, ad.pnorm(x, log=True))
    np.testing.assert_array_equal(lup, ad.pnorm(x, lower_tail=False, log=True))
    s_lo, s_up = ad.pnorm_both(1.5)
    assert isinstance(s_lo, np.float64)


def test_lgammafn_sign():
    v, s = ad.lgammafn_sign(np.array([-0.5, 0.5, -1.5, 3.0]))
    np.testing.assert_allclose(v, ad.lgammafn(np.array([-0.5, 0.5, -1.5, 3.0])))
    np.testing.assert_array_equal(s, [-1.0, 1.0, 1.0, 1.0])
    assert s.dtype == np.float64


def test_logspace_sum():
    a = np.log(np.array([[1.0, 2.0, 3.0], [1e-300, 1e-300, 1e-300]]))
    r = ad.logspace_sum(a)
    np.testing.assert_allclose(r, [np.log(6.0), np.log(3e-300)])
    assert ad.logspace_sum(a, axis=0).shape == (3,)
    assert isinstance(ad.logspace_sum([0.0, 0.0]), np.float64)
    assert ad.logspace_sum([0.0, 0.0]) == pytest.approx(np.log(2.0))
    big = np.full(4, 1e4)
    assert ad.logspace_sum(big) == pytest.approx(1e4 + np.log(4.0))


def approx_mp(got, want):
    want = float(want)
    return got == pytest.approx(want, rel=1e-13, abs=1e-300)


@pytest.mark.parametrize("x", [-0.99, -0.5, -0.1, -1e-5, -1e-10, 0.0, 1e-10, 1e-5, 0.1, 0.5, 1.0, 10.0, 1e5, 1e10])
def test_log1pmx(x):
    assert approx_mp(ad.log1pmx(x), mpmath.log1p(mpmath.mpf(x)) - mpmath.mpf(x))


@pytest.mark.parametrize("x", [-800.0, -40.0, -1.0, 0.0, 1.0, 18.0, 33.4, 40.0, 700.0, 1e10])
def test_log1pexp(x):
    assert approx_mp(ad.log1pexp(x), mpmath.log1p(mpmath.exp(mpmath.mpf(x))))


@pytest.mark.parametrize("x", [-0.4, -1e-3, -1e-10, 0.0, 1e-12, 1e-5, 0.1, 0.4999, 0.5, 2.0, 100.0])
def test_lgamma1p(x):
    assert approx_mp(ad.lgamma1p(x), mpmath.loggamma(1 + mpmath.mpf(x)))


@pytest.mark.parametrize("lx, ly", [(0.0, 0.0), (-1000.0, -1000.0), (-1000.0, -1030.0), (700.0, 690.0), (-2.0, -50.0), (5.0, -np.inf)])
def test_logspace_add_sub(lx, ly):
    assert approx_mp(ad.logspace_add(lx, ly), mpmath.log(mpmath.exp(lx) + mpmath.exp(ly)))
    if ly < lx:
        assert approx_mp(ad.logspace_sub(lx, ly), mpmath.log(mpmath.exp(lx) - mpmath.exp(ly)))
    assert ad.logspace_add(lx, ly) == pytest.approx(np.logaddexp(lx, ly))


def test_free_caches_is_idempotent():
    ad.psignrank(3, 10)
    ad.free_caches()
    ad.free_caches()
    assert ad.psignrank(3, 10) == pytest.approx(5 / 1024)
