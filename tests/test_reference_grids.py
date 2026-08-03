import json
import struct
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path

import pytest

import accudist as ad
from accudist._platform import platform_id
from oracle_bits import can_apply_ulp_waiver, same_oracle_value


DATA = Path(__file__).parent / "data" / platform_id()
if not DATA.is_dir():
    raise RuntimeError(
        f"no committed R 4.5.2 oracle vectors for {platform_id()}; release is blocked"
    )
FILES = sorted(path for path in DATA.glob("*.jsonl") if path.name != "ppois.jsonl")


def load_waivers():
    document = tomllib.loads((Path(__file__).parent / "ulp_waivers.toml").read_text())
    result = {}
    for waiver in document.get("waiver", []):
        assert 0 < waiver["max_ulp"] <= 4
        assert waiver["reason"]
        if platform_id() in waiver["platforms"]:
            result[waiver["func"]] = waiver["max_ulp"]
    return result


WAIVERS = load_waivers()


def ordered_bits(raw):
    bits = int.from_bytes(raw, "big")
    return (~bits & ((1 << 64) - 1)) if bits >> 63 else bits | (1 << 63)


def result_bits(value):
    if isinstance(value, tuple):
        return [struct.pack(">d", float(item)) for item in value]
    return struct.pack(">d", float(value))


def vectors():
    for path in FILES:
        lines = path.read_text().splitlines()
        metadata = json.loads(lines[0])["meta"]
        assert metadata["r_version"] == ad.__r_version__
        assert metadata["platform"] == platform_id()
        function = getattr(ad, metadata["function"])
        for index, line in enumerate(lines[1:]):
            case = json.loads(line)
            yield f"{metadata['function']}[{index}]", function, case


@pytest.mark.parametrize(("case_id", "function", "case"), list(vectors()), ids=lambda item: item if isinstance(item, str) else None)
def test_deterministic_functions_match_r_452_bit_for_bit(case_id, function, case):
    name = case_id.partition("[")[0]
    encoded = case["hex"]
    expected = (
        [bytes.fromhex(item.removeprefix("0x")) for item in encoded]
        if isinstance(encoded, list)
        else bytes.fromhex(encoded.removeprefix("0x"))
    )
    with ad.errstate(all="ignore"):
        actual = function(*case["args"], **case["kwargs"])
    actual = result_bits(actual)
    if isinstance(expected, list):
        assert len(actual) == len(expected)
        assert all(
            same_oracle_value(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected, strict=True)
        )
    elif same_oracle_value(actual, expected):
        pass
    elif name in WAIVERS and can_apply_ulp_waiver(actual, expected):
        assert abs(ordered_bits(actual) - ordered_bits(expected)) <= WAIVERS[name]
    else:
        assert actual == expected
