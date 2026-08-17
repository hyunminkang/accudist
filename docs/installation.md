# Installation

## Install from PyPI

Use a supported CPython interpreter in a virtual environment:

```console
python -m pip install --upgrade pip
python -m pip install accudist
```

`accudist` supports CPython 3.10 through 3.14 and requires NumPy 1.25 or newer.
Binary wheels are built for 64-bit manylinux-compatible (glibc) Linux, macOS, and
Windows. Alpine and other musl-based Linux systems currently build from the source
distribution. Free-threaded wheels are built for the supported free-threaded CPython
releases.

Confirm the installed versions:

```console
python -c "import accudist; print(accudist.__version__, accudist.__r_version__)"
```

## Build from source

A source build requires a working C compiler, Python development headers, and the
build dependencies declared in `pyproject.toml`. The normal pip build-isolation
flow installs the Python-side build tools automatically:

```console
python -m pip install --upgrade pip
python -m pip install .
```

The R nmath sources are included in the source distribution; a separate R
installation is not required.

## Install optional tools

From a repository checkout, install the test or documentation dependencies with:

```console
python -m pip install '.[test]'
python -m pip install '.[docs]'
```

See [troubleshooting](troubleshooting.md) if pip attempts an unexpected source build
or cannot find a compatible wheel.

## Licence

`accudist` and its vendored R nmath sources are distributed under
GPL-2.0-or-later. Review that licence before redistributing a work that incorporates
the package.
