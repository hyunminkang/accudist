#!/usr/bin/env python3
"""Check functions.toml against Rmath.h and vendored C definitions."""

from __future__ import annotations

import re
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "functions.toml"
HEADER = ROOT / "vendor" / "nmath" / "include" / "Rmath.h"
SOURCE = ROOT / "vendor" / "nmath" / "src"

# Exported support hooks and helpers intentionally outside the public inventory.
INFRASTRUCTURE = {
    "R_unif_index",
    "Rtanpi",
    "log1mexp",
    "pow1p",
    "signrank_free",
    "wilcox_free",
    # Rmath.h declares this symbol but R itself composes non-central rbeta.
    "rnbeta",
}


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def header_functions(text: str) -> set[str]:
    clean = strip_comments(text)
    pattern = re.compile(
        r"(?m)^\s*(?:extern\s+)?(?:double|int|void|unsigned int|long double)"
        r"\s+([A-Za-z_]\w*)\s*\([^;{{}}]*\)\s*;"
    )
    return set(pattern.findall(clean))


def definitions() -> set[str]:
    pattern = re.compile(
        r"(?m)^\s*(?:attribute_hidden\s+)?(?:static\s+)?"
        r"(?:double|int|void|unsigned int|LDOUBLE)\s*\n?\s*"
        r"([A-Za-z_]\w*)\s*\([^;]*?\)\s*\n?\s*\{"
    )
    result: set[str] = set()
    for source in SOURCE.rglob("*.c"):
        result.update(pattern.findall(strip_comments(source.read_text())))
    return result


def inventory(data: dict) -> tuple[set[str], set[str]]:
    accounted: set[str] = set()
    referenced: set[str] = set()
    for function in data["func"]:
        for key in ("call", "call_ncp", "call_mu"):
            call = function.get(key, {})
            symbol = call.get("c_symbol")
            if symbol:
                accounted.add(symbol)
                referenced.add(symbol)
    for section in ("bespoke", "rng_primitive"):
        for entry in data.get(section, []):
            accounted.add(entry["c_symbol"])
            referenced.add(entry["c_symbol"])
    accounted.update(entry["c_symbol"] for entry in data.get("excluded", []))
    return accounted, referenced


def macro_aliases(text: str) -> dict[str, str]:
    return dict(re.findall(r"(?m)^#\s*define\s+(\w+)\s+(\w+)\s*$", text))


def main() -> None:
    data = tomllib.loads(MANIFEST.read_text())
    header_text = HEADER.read_text()
    declared = header_functions(header_text)
    accounted, referenced = inventory(data)
    aliases = macro_aliases(header_text)
    defined = definitions()

    unaccounted = sorted(declared - accounted - INFRASTRUCTURE)
    missing: list[str] = []
    for symbol in sorted(referenced):
        if symbol in defined or aliases.get(symbol) in defined:
            continue
        missing.append(symbol)

    print(f"unaccounted symbols: {len(unaccounted)}")
    for symbol in unaccounted:
        print(f"  {symbol}")
    print(f"referenced symbols declared but not defined: {len(missing)}")
    for symbol in missing:
        print(f"  {symbol}")
    raise SystemExit(bool(unaccounted or missing))


if __name__ == "__main__":
    main()
