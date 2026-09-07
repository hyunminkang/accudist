import json
from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


def load_reference(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text())


def reference_functions() -> list[str]:
    return sorted(p.stem for p in DATA.glob("*.json"))


def as_float(v):
    """Decode a JSON reference value ('nan', 'inf', '-inf' or a number/string)."""
    if isinstance(v, bool):
        return v
    return float(v)


@pytest.fixture
def ignore_nmath_conditions():
    import accudist as ad

    with ad.errstate(all="ignore"):
        yield
