import json
import platform
import struct
import tomllib
from pathlib import Path

import pytest

import accudist as ad


DATA = Path(__file__).parent / "data"
FILES = sorted(path for path in DATA.glob("*.jsonl") if path.name != "ppois.jsonl")


def platform_id():
    system = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(
        platform.system(), platform.system().lower()
    )
    machine = platform.machine().lower()
    architecture = "arm64" if machine in {"arm64", "aarch64"} else machine
    return f"{system}-{architecture}"


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


def vectors():
    for path in FILES:
        lines = path.read_text().splitlines()
        metadata = json.loads(lines[0])["meta"]
        assert metadata["r_version"] == ad.__r_version__
        function = getattr(ad, metadata["function"])
        for index, line in enumerate(lines[1:]):
            case = json.loads(line)
            yield f"{metadata['function']}[{index}]", function, case


@pytest.mark.parametrize(("case_id", "function", "case"), list(vectors()), ids=lambda item: item if isinstance(item, str) else None)
def test_deterministic_functions_match_r_452_bit_for_bit(case_id, function, case):
    name = case_id.partition("[")[0]
    expected = bytes.fromhex(case["hex"].removeprefix("0x"))
    with ad.errstate(all="ignore"):
        actual = function(*case["args"], **case["kwargs"])
    actual = struct.pack(">d", float(actual))
    if actual != expected and name in WAIVERS:
        assert abs(ordered_bits(actual) - ordered_bits(expected)) <= WAIVERS[name]
    else:
        assert actual == expected
