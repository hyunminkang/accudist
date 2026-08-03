import sys
import sysconfig

import pytest

import accudist  # noqa: F401


@pytest.mark.skipif(
    not sysconfig.get_config_var("Py_GIL_DISABLED"),
    reason="requires a free-threaded CPython build",
)
def test_import_does_not_enable_the_gil():
    assert not sys._is_gil_enabled()
