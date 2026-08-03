#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for source in sorted((root / "vendor" / "nmath" / "src").rglob("*.c")):
    print(source.relative_to(root).as_posix())

