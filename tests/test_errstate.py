"""Error-word plumbing: warnings, errstate, MemoryError instead of exit(1), silence."""

import subprocess
import sys
import warnings

import numpy as np
import pytest

import accudist as ad
from accudist import _ufuncs


def test_domain_error_warns_and_returns_nan():
    with pytest.warns(ad.AccudistDomainWarning, match="qbinom"):
        r = ad.qbinom(0.5, -1, 0.5)
    assert np.isnan(r)


def test_errstate_raise_and_ignore():
    with ad.errstate(domain="raise"):
        with pytest.raises(ad.AccudistDomainError):
            ad.qbinom(0.5, -1, 0.5)
    with ad.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("error")
        assert np.isnan(ad.qbinom(0.5, -1, 0.5))


def test_errstate_nesting_and_decorator():
    assert ad.get_errstate()["domain"] == "warn"
    with ad.errstate(all="ignore"):
        assert ad.get_errstate()["domain"] == "ignore"
        with ad.errstate(domain="raise"):
            assert ad.get_errstate() == {**ad.get_errstate(), "domain": "raise"}
            assert ad.get_errstate()["range"] == "ignore"
        assert ad.get_errstate()["domain"] == "ignore"
    assert ad.get_errstate()["domain"] == "warn"

    @ad.errstate(domain="raise")
    def f():
        return ad.qnorm(2.0)

    with pytest.raises(ad.AccudistDomainError):
        f()


def test_errstate_validation():
    with pytest.raises(TypeError):
        ad.errstate(bogus="warn")
    with pytest.raises(ValueError):
        ad.errstate(domain="explode")


def test_exceptions_are_value_errors():
    assert issubclass(ad.AccudistDomainError, ValueError)
    assert issubclass(ad.AccudistDomainWarning, RuntimeWarning)


def test_errstate_is_thread_local():
    import threading

    seen = {}

    def worker():
        seen["policy"] = ad.get_errstate()["domain"]

    with ad.errstate(domain="raise"):
        t = threading.Thread(target=worker)
        t.start()
        t.join()
    assert seen["policy"] == "warn"


def test_nmath_message_warning_carries_r_text():
    with pytest.warns(ad.AccudistWarning, match="must be integer, rounded"):
        assert ad.choose(5, 2.4) == 10.0
    with ad.errstate(message="ignore"), warnings.catch_warnings():
        warnings.simplefilter("error")
        ad.choose(5, 2.4)


def test_precision_and_underflow_ignored_by_default():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ad.beta(1e5, 1e5)  # underflows to 0 with ME_UNDERFLOW in nmath


def test_flag_is_sticky_per_call_only():
    with pytest.warns(ad.AccudistDomainWarning):
        ad.qnorm(np.array([0.5, 2.0, 0.1]))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ad.qnorm(0.5)  # previous call's flag must not leak


def test_allocation_failure_raises_memory_error():
    """The regression guard for the exit(1) patch: nmath must not kill the process."""
    ad.free_caches()
    _ufuncs._set_fail_calloc_after(0)
    with pytest.raises(MemoryError, match="signrank"):
        ad.psignrank(5, 40)
    _ufuncs._set_fail_calloc_after(-1)
    assert ad.psignrank(5, 40) == pytest.approx(9.0949470177292824e-12, rel=1e-8)  # R 4.5.2

    ad.free_caches()
    _ufuncs._set_fail_calloc_after(0)
    with pytest.raises(MemoryError, match="wilcox"):
        ad.pwilcox(10, 4, 6)
    _ufuncs._set_fail_calloc_after(-1)
    assert ad.pwilcox(10, 4, 6) == pytest.approx(0.38095238095238093)

    _ufuncs._set_fail_calloc_after(0)
    with pytest.raises(MemoryError, match="bessel"):
        ad.bessel_j(1.0, 2.5)
    _ufuncs._set_fail_calloc_after(-1)


def test_nothing_is_written_to_stdout_or_stderr(tmp_path):
    """Regression guard for the printf patch: provoke every warning path in a subprocess."""
    code = r"""
import warnings, accudist as ad, numpy as np
warnings.simplefilter("ignore")
ad.qbinom(0.5, -1, 0.5); ad.choose(5, 2.4); ad.pbinom(3, 10.5, 0.3)
ad.pchisq(1e3, 1e-3, ncp=1e4); ad.bessel_j(1.0, 1e6); ad.qbeta(1e-300, 1e-3, 1e3)
ad.pnbeta if False else None
ad.rmultinom(1, 10, [0.5, 0.5])
try:
    ad.rmultinom(1, 10, [0.5, 0.6])
except ValueError:
    pass
"""
    # cwd=tmp_path: the repo root would shadow the installed package with the source tree
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=tmp_path)
    assert res.stdout == "" and res.stderr == ""
