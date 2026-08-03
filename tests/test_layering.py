from pathlib import Path


def test_runtime_package_never_imports_scipy():
    package = Path(__file__).parents[1] / "accudist"
    offenders = []
    for source in package.rglob("*.py"):
        text = source.read_text()
        if "import scipy" in text or "from scipy" in text:
            offenders.append(source.relative_to(package).as_posix())
    assert offenders == []


def test_generated_api_uses_only_documented_runtime_layers():
    source = (Path(__file__).parents[1] / "accudist" / "_api.py").read_text()
    assert "from . import _dispatch, _errstate, _rng, _ufuncs" in source
    assert "scipy" not in source

