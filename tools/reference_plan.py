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


PRIMES = [37, 43, 47, 53, 59, 61, 67, 71]


def value(param: str, index: int, name: str, position: int):
    if name.endswith("signrank") and param == "n":
        choices = [-1.0, 0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 100.0, math.nan]
        return choices[(index * PRIMES[position]) % len(choices)]
    if name.endswith("wilcox") and param in {"m", "n"}:
        choices = [-1.0, 0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, math.nan]
        return choices[(index * PRIMES[position]) % len(choices)]
    if param == "p":
        probabilities = REFERENCE_VALUES["p"]
        return probabilities[(index * PRIMES[position]) % len(probabilities)]
    if param == "n" and name in {"choose", "lchoose"}:
        choices = [-10.5, -3.0, -1.0, 0.0, 1e-10, 0.5, 1.0, 2.0, 3.0,
                   5.0, 8.0, 10.0, 20.0, 50.0, 100.0, 1e3, 1e5, 1e10, math.inf]
        return choices[(index * PRIMES[position]) % len(choices)]
    if param == "k" and name in {"choose", "lchoose"}:
        choices = [-1e10, -100.0, -20.0, -5.0, -1.0, -1e-10, 0.0, 1e-10,
                   0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0,
                   1e3, 1e5, 1e10, math.inf, -math.inf, math.nan]
        return choices[(index * PRIMES[position]) % len(choices)]
    choices = REFERENCE_VALUES.get(param, [0.5, 1.0, 2.0, 5.0])
    return choices[(index * PRIMES[position]) % len(choices)]


def r_number(item) -> str:
    if isinstance(item, bool):
        return "TRUE" if item else "FALSE"
    if math.isnan(float(item)):
        return "NaN"
    if math.isinf(float(item)):
        return "-Inf" if float(item) < 0 else "Inf"
    # Hexadecimal literals round-trip identically through Python's and R's
    # parsers; decimal 17-digit spellings can land on adjacent doubles in R.
    return float(item).hex()


def make_case(function: dict, index: int):
    name = function["name"]
    flags = {flag: bool((index // (2 ** position)) % 2) for position, flag in enumerate(function["flags"])}
    cursor = index // (2 ** len(function["flags"]))
    branch = None
    if function.get("dispatch") in {"ncp", "prob_or_mu"} or function.get("alias") == "rate_scale":
        branch = cursor % 2
        cursor //= 2
    args = []
    kwargs = {}
    r_args = []
    for position, param in enumerate(function["params"]):
        py = param["py"]
        if function.get("dispatch") == "prob_or_mu" and py in {"prob", "mu"}:
            continue
        if function.get("alias") == "rate_scale" and py in {"rate", "scale"}:
            continue
        item = value(py, cursor, name, position)
        if py == "p" and flags.get("log", False):
            item = -math.inf if item == 0.0 else (math.nan if item < 0.0 else math.log(item))
        args.append(item)
        r_args.append(r_number(item))

    if function.get("dispatch") == "prob_or_mu":
        key = "prob" if branch == 0 else "mu"
        item = value(key, cursor, name, 2)
        kwargs[key] = item
        r_args.append(f"{key}={r_number(item)}")
    if function.get("alias") == "rate_scale":
        key = "rate" if branch == 0 else "scale"
        item = value(key, cursor, name, 2)
        kwargs[key] = item
        r_args.append(f"{key}={r_number(item)}")
    if function.get("dispatch") == "ncp" and branch == 1:
        item = value("ncp", cursor, name, len(function["params"]))
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
        seen = set()
        for index in range(count):
            args, kwargs, expression = make_case(function, index)
            encoded_args = json.dumps(args, separators=(",", ":"), allow_nan=True)
            encoded_kwargs = json.dumps(kwargs, separators=(",", ":"), allow_nan=True)
            identity = (encoded_args, encoded_kwargs)
            if identity in seen:
                raise SystemExit(f"duplicate reference case for {function['name']}: {identity}")
            seen.add(identity)
            print(function["name"], encoded_args, encoded_kwargs, expression, sep="\t")


if __name__ == "__main__":
    main()
