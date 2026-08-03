#!/usr/bin/env python3
"""Emit deterministic R reference calls from the functions manifest."""

from __future__ import annotations

import argparse
import json
import math
import tomllib
from pathlib import Path

from grids import REFERENCE_VALUES


ROOT = Path(__file__).resolve().parents[1]


SPECIAL_R = {
    "gammafn": "gamma",
    "lgammafn": "lgamma",
    "tetragamma": "psigamma",
    "pentagamma": "psigamma",
    "bessel_j": "besselJ",
    "bessel_y": "besselY",
    "bessel_i": "besselI",
    "bessel_k": "besselK",
    "fprec": "accudist_ref_fprec",
    "fround": "accudist_ref_fround",
    "fsign": "accudist_ref_fsign",
    "ftrunc": "accudist_ref_ftrunc",
    "log1pmx": "accudist_ref_log1pmx",
    "log1pexp": "accudist_ref_log1pexp",
    "lgamma1p": "accudist_ref_lgamma1p",
    "logspace_add": "accudist_ref_logspace_add",
    "logspace_sub": "accudist_ref_logspace_sub",
    "tanpi": "accudist_ref_tanpi",
}


def value(param: str, index: int, name: str):
    if param == "p":
        probabilities = REFERENCE_VALUES["p"]
        return probabilities[index % len(probabilities)]
    if param == "n" and name in {"choose", "lchoose"}:
        return [1.0, 5.0, 10.0, 50.0][index % 4]
    return REFERENCE_VALUES.get(param, [0.5, 1.0, 2.0, 5.0])[index % len(REFERENCE_VALUES.get(param, [0.5, 1.0, 2.0, 5.0]))]


def r_number(item) -> str:
    if isinstance(item, bool):
        return "TRUE" if item else "FALSE"
    if math.isinf(float(item)):
        return "-Inf" if float(item) < 0 else "Inf"
    # Hexadecimal literals round-trip identically through Python's and R's
    # parsers; decimal 17-digit spellings can land on adjacent doubles in R.
    return float(item).hex()


def make_case(function: dict, index: int):
    name = function["name"]
    flags = {"lower_tail": index % 2 == 0, "log": (index // 2) % 2 == 1}
    args = []
    kwargs = {}
    r_args = []
    for param in function["params"]:
        py = param["py"]
        if function.get("dispatch") == "prob_or_mu" and py in {"prob", "mu"}:
            continue
        if function.get("alias") == "rate_scale" and py in {"rate", "scale"}:
            continue
        item = value(py, index, name)
        if py == "p" and flags["log"]:
            item = math.log(item)
        args.append(item)
        r_args.append(r_number(item))

    if function.get("dispatch") == "prob_or_mu":
        key = "prob" if index % 2 == 0 else "mu"
        item = value(key, index, name)
        kwargs[key] = item
        r_args.append(f"{key}={r_number(item)}")
    if function.get("alias") == "rate_scale":
        key = "rate" if index % 2 == 0 else "scale"
        item = value(key, index, name)
        kwargs[key] = item
        r_args.append(f"{key}={r_number(item)}")
    if function.get("dispatch") == "ncp" and index % 2:
        item = value("ncp", index, name)
        kwargs["ncp"] = item
        r_args.append(f"ncp={r_number(item)}")
    for flag in function["flags"]:
        kwargs[flag] = flags[flag]
        r_name = "lower.tail" if flag == "lower_tail" else ("log.p" if function["kind"] in {"p", "q"} else "log")
        r_args.append(f"{r_name}={r_number(flags[flag])}")

    r_name = SPECIAL_R.get(name, name)
    if name == "tetragamma":
        r_args.append("deriv=2")
    elif name == "pentagamma":
        r_args.append("deriv=3")
    if name in {"bessel_i", "bessel_k"}:
        r_args[-1] = f"expon.scaled={r_args[-1]}"
    if r_name.startswith("accudist_ref_"):
        expression = f'.Call("{r_name}",{",".join(r_args)})'
    else:
        expression = f"{r_name}({','.join(r_args)})"
    return args, kwargs, expression


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    options = parser.parse_args()
    data = tomllib.loads((ROOT / "docs" / "functions.toml").read_text())
    functions = [
        item for item in data["func"]
        if item["kind"] != "r" and item["milestone"] in {"M2", "M3"}
        and (not options.only or item["name"] == options.only)
    ]
    if options.only and not functions:
        raise SystemExit(f"unknown or non-deterministic function: {options.only}")
    for function in functions:
        count = 400 if function["name"] == "ppois" else 200
        for index in range(count):
            args, kwargs, expression = make_case(function, index)
            print(function["name"], json.dumps(args, separators=(",", ":"), allow_nan=False),
                  json.dumps(kwargs, separators=(",", ":"), allow_nan=False), expression, sep="\t")


if __name__ == "__main__":
    main()
