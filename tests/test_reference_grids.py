import json
import struct
from pathlib import Path

import pytest

import accudist as ad


DATA = Path(__file__).parent / "data"
FILES = sorted(path for path in DATA.glob("*.jsonl") if path.name != "ppois.jsonl")


def vectors():
    for path in FILES:
        lines = path.read_text().splitlines()
        metadata = json.loads(lines[0])["meta"]
        assert metadata["r_version"] == ad.__r_version__
        function = getattr(ad, metadata["function"])
        for index, line in enumerate(lines[1:]):
            case = json.loads(line)
            yield f"{metadata['function']}[{index}]", function, case


@pytest.mark.parametrize(("case_id", "function", "case"), vectors(), ids=lambda item: item if isinstance(item, str) else None)
def test_deterministic_functions_match_r_452_bit_for_bit(case_id, function, case):
    del case_id
    expected = bytes.fromhex(case["hex"].removeprefix("0x"))
    with ad.errstate(all="ignore"):
        actual = function(*case["args"], **case["kwargs"])
    assert struct.pack(">d", float(actual)) == expected
