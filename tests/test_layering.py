"""Module boundaries: no scipy anywhere in the package; compat uses the public API only."""

import pathlib
import re
import subprocess
import sys

PKG = pathlib.Path(__file__).resolve().parents[1] / "accudist"


def test_nothing_in_the_package_imports_scipy():
    for path in PKG.rglob("*.py"):
        text = path.read_text()
        assert not re.search(r"^\s*(import|from)\s+scipy", text, re.M), path


def test_compat_only_uses_the_public_namespace():
    for path in (PKG / "compat").rglob("*.py"):
        text = path.read_text()
        assert "_ufuncs" not in text, path
        assert not re.search(r"from \.\.(_api|_core|_errstate|_bespoke)", text), path


def test_import_does_not_pull_in_scipy():
    code = "import sys, accudist; sys.exit(int('scipy' in sys.modules))"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
