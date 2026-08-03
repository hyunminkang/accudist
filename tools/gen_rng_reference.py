#!/usr/bin/env python3
"""Generate the platform-specific, self-referential standalone Rmath RNG vector."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import struct

import accudist as ad
from accudist._platform import platform_id


ROOT = Path(__file__).resolve().parents[1]
SEED_CONTRACT = ROOT / "tests" / "data" / "rng" / "seed-state.json"


def _hex_values(values) -> list[str]:
    return [f"0x{struct.pack('>d', float(value)).hex()}" for value in values]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    runtime_platform = platform_id()
    requested_platform = os.environ.get(
        "ACCUDIST_ORACLE_PLATFORM", runtime_platform
    )
    if requested_platform != runtime_platform:
        raise SystemExit(
            "refusing to label RNG output for "
            f"{requested_platform}; this interpreter is running on {runtime_platform}"
        )

    seed_contract = json.loads(SEED_CONTRACT.read_text())
    if seed_contract["meta"]["r_version"] != ad.__r_version__:
        raise SystemExit("the RNG seed-state contract has the wrong R version")

    cases = []
    for expected in seed_contract["cases"]:
        function = expected["function"]
        seed = expected["seed"]
        function_args = expected["args"]
        rng = ad.RNG(*seed)
        values = getattr(rng, function)(*function_args)
        final_seed = list(rng.get_seed())
        if final_seed != expected["final_seed"]:
            raise SystemExit(
                f"{function} produced seed state {final_seed}, "
                f"expected {expected['final_seed']}"
            )
        cases.append(
            {
                "function": function,
                "seed": list(seed),
                "args": list(function_args),
                "hex": _hex_values(values),
                "final_seed": final_seed,
            }
        )

    document = {
        "meta": {
            "oracle": "self-referential accudist standalone Rmath stream",
            "r_version": ad.__r_version__,
            "platform": runtime_platform,
            "note": (
                "Sampling algorithms are R's; this Marsaglia-MultiCarry stream "
                "is not R set.seed()."
            ),
        },
        "cases": cases,
    }
    output = args.output or ROOT / "tests" / "data" / runtime_platform / "rng.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2) + "\n")


if __name__ == "__main__":
    main()
