#!/usr/bin/env python3
"""Vendor R's nmath sources into vendor/nmath/ (maintainer tool, not a build step).

Steps:
  1. read vendor/VENDOR.toml (R version, tarball URL, SHA-256)
  2. download the tarball (or use --tarball PATH) and verify the hash
  3. extract src/nmath/*.{c,h}, standalone/sunif.c, the R_ext headers nmath
     needs, and COPYING into vendor/nmath/
  4. generate vendor/nmath/include/Rmath.h from src/include/Rmath.h0.in
  5. apply vendor/patches/*.patch in lexical order with `patch -p1`

Vendored files are otherwise pristine.  All accudist-specific changes live in
vendor/patches/ so that bumping the R version is mechanical: edit VENDOR.toml,
re-run this script, fix any patch that no longer applies.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
NMATH = VENDOR / "nmath"
PATCHES = VENDOR / "patches"

# R_ext headers that nmath.h / Rmath.h pull in when built standalone.
R_EXT_HEADERS = ["Arith.h", "Boolean.h", "Error.h", "Memory.h", "Print.h", "Random.h", "RS.h", "Utils.h", "libextern.h"]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> None:
    print(f"downloading {url}")
    with urllib.request.urlopen(url) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def extract(tar: tarfile.TarFile, member: str) -> bytes:
    fh = tar.extractfile(member)
    if fh is None:
        raise SystemExit(f"missing member in tarball: {member}")
    return fh.read()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tarball", type=Path, help="use an already-downloaded R tarball")
    ap.add_argument("--no-patch", action="store_true", help="extract only; do not apply patches")
    args = ap.parse_args()

    meta = tomllib.loads((VENDOR / "VENDOR.toml").read_text())["r"]
    version, url, sha = meta["version"], meta["url"], meta["sha256"]

    tarball = args.tarball or (VENDOR / f"R-{version}.tar.gz")
    if not tarball.exists():
        fetch(url, tarball)
    got = sha256_of(tarball)
    if got != sha:
        raise SystemExit(f"SHA-256 mismatch for {tarball}\n  expected {sha}\n  got      {got}")
    print(f"verified {tarball.name} ({sha[:12]}...)")

    if NMATH.exists():
        shutil.rmtree(NMATH)
    (NMATH / "src").mkdir(parents=True)
    (NMATH / "include" / "R_ext").mkdir(parents=True)

    prefix = f"R-{version}/"
    with tarfile.open(tarball, "r:gz") as tar:
        names = set(tar.getnames())
        n_src = 0
        for name in sorted(names):
            if not name.startswith(prefix + "src/nmath/"):
                continue
            rel = name[len(prefix + "src/nmath/"):]
            if "/" in rel or not (rel.endswith(".c") or rel.endswith(".h")):
                continue  # skip standalone/, Makefile.in, etc.
            (NMATH / "src" / rel).write_bytes(extract(tar, name))
            n_src += 1
        # the standalone uniform generator (Marsaglia-MultiCarry) + seed API
        (NMATH / "src" / "sunif.c").write_bytes(extract(tar, prefix + "src/nmath/standalone/sunif.c"))
        for hdr in R_EXT_HEADERS:
            (NMATH / "include" / "R_ext" / hdr).write_bytes(extract(tar, prefix + f"src/include/R_ext/{hdr}"))
        (NMATH / "COPYING").write_bytes(extract(tar, prefix + "COPYING"))
        template = extract(tar, prefix + "src/include/Rmath.h0.in").decode()

    rmath_h = template.replace("@PACKAGE_VERSION@", version).replace(
        "@RMATH_HAVE_WORKING_LOG1P@", "#define HAVE_WORKING_LOG1P 1"
    )
    if "@" in rmath_h.replace("@R-project", ""):
        leftover = [ln for ln in rmath_h.splitlines() if "@" in ln and "R-project" not in ln]
        raise SystemExit("unsubstituted template markers in Rmath.h:\n" + "\n".join(leftover))
    (NMATH / "include" / "Rmath.h").write_text(rmath_h)
    print(f"extracted {n_src} nmath sources + sunif.c, {len(R_EXT_HEADERS)} R_ext headers, Rmath.h, COPYING")

    if args.no_patch:
        return 0
    for patch in sorted(PATCHES.glob("*.patch")):
        print(f"applying {patch.name}")
        res = subprocess.run(
            ["patch", "-p1", "--no-backup-if-mismatch", "-d", str(NMATH), "-i", str(patch)],
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            sys.stderr.write(res.stdout + res.stderr)
            raise SystemExit(f"patch {patch.name} failed to apply; do not edit vendored files in place")
    # patch(1) may leave .orig/.rej files on fuzz; remove any that appear.
    for stray in list(NMATH.rglob("*.orig")) + list(NMATH.rglob("*.rej")):
        stray.unlink()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
