"""Build accudist._ufuncs: vendored R nmath + shim + generated ufunc table.

Everything else (metadata, dependencies) is in pyproject.toml. A C compiler and
the NumPy headers are the only build requirements; there is no code generation
at build time (generated files are committed).
"""

import glob
import os
import sys

import numpy
from setuptools import Extension, setup

HERE = os.path.dirname(os.path.abspath(__file__))
NMATH_SRC = os.path.join("vendor", "nmath", "src")

sources = sorted(glob.glob(os.path.join(NMATH_SRC, "*.c")))
sources += [
    os.path.join("src", "accudist_shim.c"),
    os.path.join("src", "_ufuncs_generated.c"),
    os.path.join("src", "_ufuncsmodule.c"),
]

define_macros = [
    ("MATHLIB_STANDALONE", "1"),
    ("HAVE_CONFIG_H", "1"),
    ("NPY_NO_DEPRECATED_API", "NPY_1_25_API_VERSION"),
]

if sys.platform == "win32":
    # MSVC: /fp:precise is the default (no contraction); C11 for _Thread_local
    # is provided through __declspec(thread) in the shim.
    extra_compile_args = ["/O2", "/std:c11"]
else:
    extra_compile_args = [
        "-O2",
        "-std=gnu11",
        # FMA contraction perturbs last bits relative to R's reference builds.
        "-ffp-contract=off",
        # Only PyInit__ufuncs needs to be visible; keeps nmath's plain C names
        # (pnorm5, ppois, ...) from colliding with any other copy of Rmath
        # loaded into the same process.
        "-fvisibility=hidden",
    ]

ext = Extension(
    "accudist._ufuncs",
    sources=sources,
    include_dirs=[
        "src",  # config.h, Rconfig.h, accudist_shim.h -- must come first
        os.path.join("vendor", "nmath", "include"),
        NMATH_SRC,
        numpy.get_include(),
    ],
    define_macros=define_macros,
    extra_compile_args=extra_compile_args,
    libraries=[] if sys.platform == "win32" else ["m"],
)

setup(ext_modules=[ext])
