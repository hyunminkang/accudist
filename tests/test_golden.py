import json
import struct
from pathlib import Path

import pytest

import accudist as ad
from accudist._platform import platform_id
from oracle_bits import matches_oracle_value


DATA = Path(__file__).parent / "data" / platform_id() / "ppois.jsonl"


def load_vectors():
    lines = DATA.read_text().splitlines()
    header = json.loads(lines[0])["meta"]
    assert header["r_version"] == ad.__r_version__
    assert header["platform"] == platform_id()
    return [json.loads(line) for line in lines[1:]]


@pytest.mark.parametrize("case", load_vectors(), ids=lambda case: str(case["args"]))
def test_ppois_matches_r_452_reference(case):
    expected = bytes.fromhex(case["hex"].removeprefix("0x"))
    with ad.errstate(all="ignore"):
        actual = ad.ppois(*case["args"], **case["kwargs"])
    assert matches_oracle_value(struct.pack(">d", float(actual)), expected)
