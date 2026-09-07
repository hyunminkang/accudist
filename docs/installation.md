# Installation

```console
pip install accudist
```
```console
uv pip install accudist       # inside a uv-managed environment
uv add accudist               # as a project dependency
```

accudist depends only on NumPy (1.25 or newer) at runtime.

## Binary wheels

Wheels are built with cibuildwheel for CPython 3.10, 3.11, 3.12, 3.13 and 3.14 on:

| platform | architectures |
|---|---|
| Linux (manylinux, glibc) | x86_64, aarch64 |
| macOS 11+ | x86_64 (Intel), arm64 (Apple silicon) |
| Windows | x86_64 (AMD64) |

That covers the overwhelming majority of users. Not covered: PyPy, musl-based
Linux (Alpine), 32-bit systems, free-threaded CPython builds, and Windows on ARM.
On those, `pip` falls back to the source distribution automatically.

## Building from source

The sdist is self-contained: R's `nmath` sources are committed under
`vendor/nmath/`, there is no code generation at build time, and nothing is
downloaded. You need

- a C compiler (gcc, clang, or MSVC 2019+; any C11 compiler),
- Python headers (`python3-dev` / `python3-devel` on Linux distributions),
- NumPy 2.x headers, which `pip` installs into the isolated build environment.

Then any of these works:

```console
pip install accudist --no-binary accudist                 # force a source build from PyPI
pip install git+https://github.com/hyunminkang/accudist   # latest main branch
git clone https://github.com/hyunminkang/accudist && pip install ./accudist
uv pip install --no-binary accudist accudist              # the same with uv
```

A source build takes about a minute. Wheels built against NumPy 2 run on NumPy
1.25+ at runtime.

!!! note "Windows"
    MSVC is the supported compiler on Windows (install "Desktop development with
    C++" from the Visual Studio Build Tools). MinGW builds are untested.

## Development install

```console
git clone https://github.com/hyunminkang/accudist && cd accudist
uv venv && source .venv/bin/activate
uv pip install setuptools numpy pytest hypothesis scipy mpmath
uv pip install --no-build-isolation -e .
pytest -q
```

`scipy` and `mpmath` are test-only dependencies; nothing under `accudist/` imports them.

## Checking the install

```pycon
>>> import accudist as ad
>>> ad.__version__, ad.__r_version__
('0.1.0', '4.5.2')
>>> ad.ppois(200, 0.1, lower_tail=False, log=True)
np.float64(-1331.454400621394)
```
