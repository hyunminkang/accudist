#!/usr/bin/env python3
"""Install the locally built wheel with uv and smoke-test that exact artifact."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheelhouse", type=Path)
    args = parser.parse_args()
    wheelhouse = args.wheelhouse.resolve()
    wheels = sorted(wheelhouse.glob("*.whl"))
    if not wheels:
        raise SystemExit("wheelhouse contains no wheels")
    with tempfile.TemporaryDirectory(prefix="accudist-wheel-test-") as temporary:
        environment = Path(temporary) / "venv"
        subprocess.run(["uv", "venv", "--python", sys.executable, str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(["uv", "pip", "install", "--python", str(python), "numpy"], check=True)
        subprocess.run(
            [
                "uv", "pip", "install", "--python", str(python), "--no-index", "--no-deps",
                "--find-links", str(wheelhouse), "accudist",
            ],
            check=True,
        )
        subprocess.run(
            [str(python), "-c", "import accudist; print(accudist.__version__)"],
            check=True,
            cwd=wheelhouse,
        )


if __name__ == "__main__":
    main()
