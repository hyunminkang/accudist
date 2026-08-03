try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path


def test_active_deviations_are_human_reviewed():
    data = tomllib.loads((Path(__file__).parent / "deviations.toml").read_text())
    for deviation in data.get("deviation", []):
        assert deviation.get("reviewed_by")
        assert deviation.get("reviewed_date")
        assert deviation.get("oracle_value")
