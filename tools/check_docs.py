#!/usr/bin/env python3
"""Check that a rendered MkDocs site contains the public entry points."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", type=Path, default=Path("site"))
    args = parser.parse_args()

    required = (
        Path("index.html"),
        Path("installation/index.html"),
        Path("quickstart/index.html"),
        Path("user-guide/index.html"),
        Path("api-reference/index.html"),
        Path("errors/index.html"),
        Path("rng/index.html"),
        Path("scipy-compat/index.html"),
        Path("troubleshooting/index.html"),
        Path("benchmarks/index.html"),
        Path("packaging/index.html"),
        Path("adr/0020-tolerant-numerical-compatibility/index.html"),
        Path("search/search_index.json"),
    )
    missing = [str(path) for path in required if not (args.site / path).is_file()]
    if missing:
        parser.error("rendered site is missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()
