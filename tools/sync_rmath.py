#!/usr/bin/env python3
"""Synchronize the pristine, patched R 4.5.2 nmath source inventory."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
CONFIG = VENDOR / "VENDOR.toml"

DIRECT_R_EXT_HEADERS = {
    "Arith.h",
    "Boolean.h",
    "Error.h",
    "Memory.h",
    "Print.h",
    "Random.h",
    "RS.h",
    "Utils.h",
    "Visibility.h",
    "libextern.h",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_bytes(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.extractfile(name)
    if member is None:
        raise RuntimeError(f"missing required R source member: {name}")
    return member.read()


def _safe_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _extract(archive_path: Path, destination: Path, version: str) -> None:
    prefix = f"R-{version}/"
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            relative = member.name.removeprefix(prefix)
            if member.isfile() and relative.startswith("src/nmath/"):
                tail = relative.removeprefix("src/nmath/")
                if "/" not in tail and tail.endswith((".c", ".h")):
                    _safe_write(destination / "src" / tail, _member_bytes(archive, member.name))
            if member.isfile() and relative == "src/nmath/standalone/sunif.c":
                _safe_write(destination / "src" / "standalone" / "sunif.c", _member_bytes(archive, member.name))

        rmath = _member_bytes(archive, prefix + "src/include/Rmath.h0.in").decode()
        rmath = rmath.replace("@PACKAGE_VERSION@", version)
        rmath = rmath.replace("@RMATH_HAVE_WORKING_LOG1P@", "# define HAVE_WORKING_LOG1P 1")
        _safe_write(destination / "include" / "Rmath.h.in", rmath.encode())
        _safe_write(destination / "include" / "Rmath.h", rmath.encode())

        for header in sorted(DIRECT_R_EXT_HEADERS):
            name = prefix + "src/include/R_ext/" + header
            _safe_write(destination / "include" / "R_ext" / header, _member_bytes(archive, name))

        _safe_write(destination / "COPYING", _member_bytes(archive, prefix + "COPYING"))

    rconfig = """/* Generated for standalone Rmath builds by tools/sync_rmath.py. */
#ifndef R_RCONFIG_H
#define R_RCONFIG_H
#define IEEE_754 1
#define R_INLINE inline
#if defined(__GNUC__) || defined(__clang__)
# define HAVE_VISIBILITY_ATTRIBUTE 1
#endif
#endif
"""
    _safe_write(destination / "include" / "Rconfig.h", rconfig.encode())
    config = """/* Standalone nmath feature checks for supported C11 toolchains. */
#ifndef ACCUDIST_CONFIG_H
#define ACCUDIST_CONFIG_H
#include <stdbool.h>
#define HAVE_LONG_DOUBLE 1
#define HAVE_NEARBYINT 1
#define HAVE_WORKING_ISFINITE 1
#endif
"""
    _safe_write(destination / "include" / "config.h", config.encode())


def _apply_patches(destination: Path) -> None:
    for patch in sorted((VENDOR / "patches").glob("[0-9][0-9][0-9][0-9]-*.patch")):
        subprocess.run(
            [
                "patch",
                "--batch",
                "--forward",
                "--fuzz=0",
                "--no-backup-if-mismatch",
                "-p1",
                "-i",
                str(patch),
            ],
            cwd=destination,
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, help="use an existing R tarball")
    args = parser.parse_args()
    config = tomllib.loads(CONFIG.read_text())
    version = config["version"]
    expected = config["sha256"]

    with tempfile.TemporaryDirectory(prefix="accudist-rmath-") as temp_name:
        temp = Path(temp_name)
        archive = args.archive or temp / f"R-{version}.tar.gz"
        if args.archive is None:
            urllib.request.urlretrieve(config["url"], archive)
        actual = _sha256(archive)
        if actual != expected:
            raise SystemExit(
                f"R source SHA-256 mismatch: expected {expected}, got {actual}"
            )
        extracted = temp / "nmath"
        _extract(archive, extracted, version)
        _apply_patches(extracted)

        target = VENDOR / "nmath"
        replacement = VENDOR / ".nmath.new"
        if replacement.exists():
            shutil.rmtree(replacement)
        shutil.copytree(extracted, replacement)
        if target.exists():
            shutil.rmtree(target)
        replacement.rename(target)

    print(f"vendored R {version} nmath ({actual})")


if __name__ == "__main__":
    main()
