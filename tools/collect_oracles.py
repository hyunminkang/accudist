#!/usr/bin/env python3
"""Collect per-platform reference artifacts downloaded by GitHub Actions."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    for artifact in sorted(args.artifacts.glob("oracle-*")):
        platform = artifact.name.removeprefix("oracle-")
        target = args.destination / platform
        target.mkdir(parents=True, exist_ok=True)
        for vector in artifact.glob("*.jsonl"):
            shutil.copy2(vector, target / vector.name)


if __name__ == "__main__":
    main()
