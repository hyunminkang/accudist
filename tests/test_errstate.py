import pytest

from accudist import _errstate, _ufuncs


def test_forced_allocation_failure_becomes_memory_error():
    with _errstate.capture("forced") as captured:
        _ufuncs._force_allocation_failure()
    with pytest.raises(MemoryError, match="accudist.forced: allocation failed"):
        captured.check()

