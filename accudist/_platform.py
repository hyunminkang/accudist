"""Canonical platform key for compiler-oracle and golden-vector selection."""

from __future__ import annotations

import platform


def platform_id() -> str:
    system = {"Darwin": "macos", "Linux": "linux", "Windows": "windows"}.get(
        platform.system(), platform.system().lower()
    )
    machine = platform.machine().lower().replace("x86-64", "x86_64")
    architecture = "arm64" if machine in {"arm64", "aarch64"} else machine
    if system == "windows" and architecture in {"amd64", "x86_64"}:
        architecture = "amd64"
    return f"{system}-{architecture}"
