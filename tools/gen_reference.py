#!/usr/bin/env python3
"""Regenerate tests/data/*.json from a local R installation.

    python tools/gen_reference.py            # all functions
    python tools/gen_reference.py ppois qt   # a subset

Requires `Rscript` on PATH; the R version is recorded in every file and must
match vendor/VENDOR.toml (override with --allow-version-mismatch when checking
a different R on purpose).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grids  # noqa: E402

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = grids.ROOT
DATA = ROOT / "tests" / "data"


def json_value(v):
    if isinstance(v, bool):
        return v
    if v != v:
        return "nan"
    if v in (grids.INF, -grids.INF):
        return "inf" if v > 0 else "-inf"
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("only", nargs="*", help="function names to regenerate (default: all)")
    ap.add_argument("--allow-version-mismatch", action="store_true")
    args = ap.parse_args()

    rscript = shutil.which("Rscript")
    if not rscript:
        raise SystemExit("Rscript not found on PATH")
    pinned = tomllib.loads((ROOT / "vendor" / "VENDOR.toml").read_text())["r"]["version"]

    selected = grids.all_cases()
    if args.only:
        missing = set(args.only) - set(selected)
        if missing:
            raise SystemExit(f"unknown functions: {sorted(missing)}")
        selected = {k: v for k, v in selected.items() if k in args.only}

    rows = []
    for name, (func, cases) in selected.items():
        for i, case in enumerate(cases):
            rows.append((f"{name}:{i}", grids.r_expr(func, case)))

    with tempfile.TemporaryDirectory() as tmp:
        cases_tsv = Path(tmp) / "cases.tsv"
        values_tsv = Path(tmp) / "values.tsv"
        cases_tsv.write_text("".join(f"{rid}\t{expr}\n" for rid, expr in rows))
        subprocess.run([rscript, str(ROOT / "tools" / "gen_reference.R"), str(cases_tsv), str(values_tsv)], check=True)
        lines = values_tsv.read_text().splitlines()

    header = lines[0].split("\t")
    r_version = f"{header[1]}.{header[2]}"
    if r_version != pinned and not args.allow_version_mismatch:
        raise SystemExit(f"R {r_version} found but vendor/VENDOR.toml pins {pinned}")
    values = dict(line.split("\t", 1) for line in lines[1:])

    DATA.mkdir(parents=True, exist_ok=True)
    n_err = 0
    for name, (func, cases) in selected.items():
        out_cases = []
        for i, case in enumerate(cases):
            val = values[f"{name}:{i}"]
            if val.startswith("ERROR:"):
                n_err += 1
                print(f"  {name}: {grids.r_expr(func, case)} -> {val}", file=sys.stderr)
                continue
            out_cases.append({
                "args": [json_value(a) for a in case["args"]],
                "kwargs": {k: json_value(v) for k, v in case["kwargs"].items()},
                "r": grids.r_expr(func, case),
                "expected": val,
            })
        doc = {"meta": {"function": name, "r_version": r_version, "generator": "tools/gen_reference.py"}, "cases": out_cases}
        (DATA / f"{name}.json").write_text(json.dumps(doc, indent=0, separators=(",", ":")) + "\n")
        print(f"{name}: {len(out_cases)} cases")
    if n_err:
        print(f"{n_err} expressions errored in R (skipped)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
