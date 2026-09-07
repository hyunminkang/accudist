#!/usr/bin/env python3
"""Verify that functions.toml accounts for every scalar symbol in Rmath.h.

Every `double f(...)`/`void f(...)` prototype in the vendored Rmath.h must appear
in functions.toml as a generated function's c_symbol, a bespoke entry, an RNG
primitive, or a documented exclusion -- and every referenced c_symbol must be
defined in some vendored .c file (rnbeta is declared but never implemented).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
RMATH_H = ROOT / "vendor" / "nmath" / "include" / "Rmath.h"
NMATH_SRC = ROOT / "vendor" / "nmath" / "src"

# helpers used by generated code / the shim, not part of the public inventory
INFRASTRUCTURE = {"wilcox_free", "signrank_free", "R_unif_index", "Rlog1p", "R_isnancpp"}
# aliases: the header declares dnorm/pnorm/qnorm as macros for these
ALIASES = {"dnorm4": "dnorm", "pnorm5": "pnorm", "qnorm5": "qnorm"}


def declared_symbols() -> set[str]:
    text = RMATH_H.read_text()
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    syms = set()
    for m in re.finditer(r"^\s*(?:double|int|void)\s+([A-Za-z_]\w*)\s*\(", text, re.M):
        syms.add(m.group(1))
    return syms


def defined_symbols() -> set[str]:
    pat = re.compile(r"^(?:double|int|void|LDOUBLE)\s+([A-Za-z_]\w*)\s*\(", re.M)
    syms = set()
    for c in NMATH_SRC.glob("*.c"):
        syms.update(pat.findall(c.read_text()))
    return syms


def main() -> int:
    manifest = tomllib.loads((ROOT / "functions.toml").read_text())
    accounted: set[str] = set()
    referenced: set[str] = set()
    for f in manifest["func"]:
        for key in ("call", "call_ncp", "call_mu"):
            c = f.get(key)
            if c and "c_symbol" in c:
                accounted.add(c["c_symbol"])
                referenced.add(c["c_symbol"])
    for section in ("bespoke", "rng_primitive"):
        for e in manifest[section]:
            accounted.add(e["c_symbol"])
            referenced.add(e["c_symbol"])
    for e in manifest["excluded"]:
        accounted.add(e["c_symbol"])
    accounted |= INFRASTRUCTURE

    declared = declared_symbols()
    defined = defined_symbols()
    ok = True

    unaccounted = sorted(s for s in declared if s not in accounted and ALIASES.get(s, s) not in accounted)
    if unaccounted:
        ok = False
        print("Rmath.h symbols not in functions.toml:", ", ".join(unaccounted))

    undefined = sorted(s for s in referenced if s not in defined and s not in {"dnorm", "pnorm", "qnorm"})
    if undefined:
        ok = False
        print("functions.toml references symbols with no definition in vendor/nmath/src:", ", ".join(undefined))

    stale = sorted(e["c_symbol"] for e in manifest["excluded"] if e["c_symbol"] not in declared)
    if stale:
        print("note: excluded symbols no longer declared in Rmath.h:", ", ".join(stale))

    print(f"{len(declared)} declared, {len(referenced)} referenced, {len(manifest['excluded'])} excluded; "
          + ("OK" if ok else "PROBLEMS FOUND"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
