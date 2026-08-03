import json
import struct
from pathlib import Path

import pytest

import accudist as ad


DATA = Path(__file__).parent / "data" / "ppois.jsonl"


def load_vectors():
    lines = DATA.read_text().splitlines()
    header = json.loads(lines[0])["meta"]
    assert header["r_version"] == ad.__r_version__
    return [json.loads(line) for line in lines[1:]]


@pytest.mark.parametrize("case", load_vectors(), ids=lambda case: str(case["args"]))
def test_ppois_matches_r_452_bit_for_bit(case):
    expected = bytes.fromhex(case["hex"].removeprefix("0x"))
    with ad.errstate(all="ignore"):
        actual = ad.ppois(
            *case["args"],
            lower_tail=bool(case["lower_tail"]),
            log=bool(case["log"]),
        )
    assert struct.pack(">d", float(actual)) == expected

