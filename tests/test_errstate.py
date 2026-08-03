import pytest
import subprocess
import sys
import textwrap

from accudist import _errstate, _ufuncs


def test_forced_allocation_failure_becomes_memory_error():
    with _errstate.capture("forced") as captured:
        _ufuncs._force_allocation_failure()
    with pytest.raises(MemoryError, match="accudist.forced: allocation failed"):
        captured.check()


@pytest.mark.skipif(
    sys.platform in {"win32", "darwin"},
    reason="RLIMIT_AS is unavailable on Windows and not enforceable on macOS",
)
def test_real_signrank_allocation_failure_never_crashes_interpreter():
    program = textwrap.dedent(
        """
        import resource
        import accudist as ad

        limit = 1024 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        try:
            ad.psignrank(1, 40000)
        except MemoryError:
            print("MemoryError")
        else:
            raise AssertionError("allocation unexpectedly succeeded")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "MemoryError\n"
