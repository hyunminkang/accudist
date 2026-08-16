#!/usr/bin/env python3
"""Generate accudist's C ufunc, public API, stubs, raw API, and manifest test."""

from __future__ import annotations

import argparse
import difflib
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "functions.toml"
GENERATED = {
    "_ufuncs.c": ROOT / "accudist" / "_ufuncs.c",
    "_api.py": ROOT / "accudist" / "_api.py",
    "_generated.pyi": ROOT / "accudist" / "_generated.pyi",
    "rmath.py": ROOT / "accudist" / "rmath.py",
    "test_manifest.py": ROOT / "tests" / "test_manifest.py",
    "api-reference.md": ROOT / "docs" / "api-reference.md",
}
BUILD_GENERATED = frozenset(GENERATED) - {"api-reference.md"}


def enabled_functions(data: dict) -> list[dict]:
    """M2 enables the whole central table after the M1 gate is green."""

    return [function for function in data["func"] if function["milestone"] in {"M2", "M3"}]


def call_entries(function: dict):
    for key in ("call", "call_ncp", "call_mu"):
        call = function.get(key)
        if call and "c_symbol" in call:
            yield key, call


def call_inputs(function: dict, call: dict) -> list[str]:
    if function["kind"] in {"d", "p", "q"}:
        values = [function["params"][0]["py"], *call["c_args"]]
    else:
        values = list(call["c_args"])
    return [*values, *function["flags"]]


def ufunc_specs(functions: list[dict]) -> dict[str, dict]:
    specs: dict[str, dict] = {}
    for function in functions:
        for _, call in call_entries(function):
            symbol = call["c_symbol"]
            inputs = call_inputs(function, call)
            flags = set(function["flags"])
            spec = {
                "symbol": symbol,
                "inputs": inputs,
                "flags": flags,
                "cache": function.get("cache"),
                "rng": function["kind"] == "r",
            }
            previous = specs.get(symbol)
            if previous and (
                previous["inputs"] != inputs
                or previous["flags"] != flags
                or previous["cache"] != spec["cache"]
                or previous["rng"] != spec["rng"]
            ):
                raise ValueError(f"inconsistent signatures for C symbol {symbol}")
            specs[symbol] = spec
    # Rmath.h exposes these helpers as part of its raw ABI.  They intentionally
    # have no public accudist wrapper, but docs/functions.toml records them as
    # raw-only exclusions and rmath.py must make them reachable.
    specs["dbinom_raw"] = {
        "symbol": "dbinom_raw",
        "inputs": ["x", "n", "p", "q", "give_log"],
        "flags": {"give_log"},
        "cache": None,
        "rng": False,
    }
    specs["dpois_raw"] = {
        "symbol": "dpois_raw",
        "inputs": ["x", "lambda_", "give_log"],
        "flags": {"give_log"},
        "cache": None,
        "rng": False,
    }
    return specs


def c_identifier(name: str) -> str:
    result = name.removesuffix("_")
    if result in {"log", "sign"}:
        result += "_arg"
    return result


def render_c(functions: list[dict]) -> str:
    loops: list[str] = []
    registrations: list[str] = []
    for symbol, spec in ufunc_specs(functions).items():
        inputs = spec["inputs"]
        flags = spec["flags"]
        declarations: list[str] = []
        call_args: list[str] = []
        for index, item in enumerate(inputs):
            name = c_identifier(item)
            if item in flags:
                # NumPy resolves Python integers as 64-bit values on 64-bit Windows,
                # where C long is only 32 bits and therefore rejects a safe cast.
                declarations.append(
                    f"        npy_int64 {name} = *(npy_int64 *)(args[{index}] + i * steps[{index}]);"
                )
                call_args.append(f"(int){name}")
            else:
                declarations.append(
                    f"        double {name} = *(double *)(args[{index}] + i * steps[{index}]);"
                )
                call_args.append(name)
        output_index = len(inputs)
        lock_before = ""
        lock_after = ""
        if spec["rng"]:
            lock_before += "    accudist_rng_acquire();\n"
            lock_after = "    accudist_rng_release();\n" + lock_after
        if spec["cache"]:
            lock_before += "    PyThread_acquire_lock(accudist_cache_lock, WAIT_LOCK);\n"
            lock_after = "    PyThread_release_lock(accudist_cache_lock);\n" + lock_after
        type_codes = ["NPY_INT64" if item in flags else "NPY_DOUBLE" for item in inputs]
        type_codes.append("NPY_DOUBLE")
        call = f"{symbol}({', '.join(call_args)})"
        loops.append(
            f"""static void
{symbol}_loop(char **args, const npy_intp *dims, const npy_intp *steps, void *data)
{{
    npy_intp n = dims[0];
    (void)data;
{lock_before}    for (npy_intp i = 0; i < n; i++) {{
{chr(10).join(declarations)}
        *(double *)(args[{output_index}] + i * steps[{output_index}]) = {call};
    }}
{lock_after}}}

static PyUFuncGenericFunction {symbol}_funcs[1] = {{{symbol}_loop}};
static void *{symbol}_data[1] = {{NULL}};
static char {symbol}_types[] = {{{', '.join(type_codes)}}};
"""
        )
        registrations.append(
            f"""    {{
        PyObject *ufunc = PyUFunc_FromFuncAndData(
            {symbol}_funcs, {symbol}_data, {symbol}_types,
            1, {len(inputs)}, 1, PyUFunc_None,
            "{symbol}", "Raw R nmath {symbol} ufunc.", 0
        );
        if (ufunc == NULL || PyModule_AddObject(module, "{symbol}", ufunc) < 0) {{
            Py_XDECREF(ufunc);
            Py_DECREF(module);
            return NULL;
        }}
    }}"""
        )

    return f"""/* GENERATED by tools/regen.py -- do not edit. */
#define PY_SSIZE_T_CLEAN
#define NPY_NO_DEPRECATED_API NPY_1_25_API_VERSION
#include <Python.h>
#include <limits.h>
#include <math.h>
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>
#include <Rmath.h>
#include "accudist_shim.h"

extern void wilcox_free(void);
extern void signrank_free(void);
extern PyThread_type_lock accudist_cache_lock;
extern PyThread_type_lock accudist_rng_lock;

{chr(10).join(loops)}
static PyObject *
py_clear_error(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    accudist_clear_error();
    Py_RETURN_NONE;
}}

static PyObject *
py_take_error(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    return PyLong_FromUnsignedLong(accudist_take_error());
}}

static PyObject *
py_force_allocation_failure(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    accudist_fatal("forced allocation failure: %d", 1);
    Py_RETURN_NONE;
}}

static PyObject *
py_pnorm_both_scalar(PyObject *self, PyObject *args)
{{
    double x, lower, upper;
    int log_p;
    (void)self;
    if (!PyArg_ParseTuple(args, "di:_pnorm_both_scalar", &x, &log_p)) return NULL;
    pnorm_both(x, &lower, &upper, 2, log_p);
    return Py_BuildValue("(dd)", lower, upper);
}}

static PyObject *
py_lgammafn_sign_scalar(PyObject *self, PyObject *args)
{{
    double x, value;
    int sign = 1;
    (void)self;
    if (!PyArg_ParseTuple(args, "d:_lgammafn_sign_scalar", &x)) return NULL;
    value = lgammafn_sign(x, &sign);
    return Py_BuildValue("(di)", value, sign);
}}

static PyObject *
py_pnorm_both_array(PyObject *self, PyObject *args)
{{
    PyObject *argument, *result;
    PyArrayObject *input, *lower, *upper;
    int log_p;
    npy_intp length;
    (void)self;
    if (!PyArg_ParseTuple(args, "Oi:_pnorm_both_array", &argument, &log_p)) return NULL;
    input = (PyArrayObject *)PyArray_FROM_OTF(argument, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (input == NULL) return NULL;
    lower = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(input), PyArray_DIMS(input), NPY_DOUBLE);
    upper = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(input), PyArray_DIMS(input), NPY_DOUBLE);
    if (lower == NULL || upper == NULL) {{
        Py_XDECREF(lower);
        Py_XDECREF(upper);
        Py_DECREF(input);
        return PyErr_NoMemory();
    }}
    length = PyArray_SIZE(input);
    for (npy_intp i = 0; i < length; i++) {{
        pnorm_both(((double *)PyArray_DATA(input))[i],
                   &((double *)PyArray_DATA(lower))[i],
                   &((double *)PyArray_DATA(upper))[i], 2, log_p);
    }}
    result = PyTuple_Pack(2, (PyObject *)lower, (PyObject *)upper);
    Py_DECREF(input);
    Py_DECREF(lower);
    Py_DECREF(upper);
    return result;
}}

static PyObject *
py_lgammafn_sign_array(PyObject *self, PyObject *argument)
{{
    PyObject *result;
    PyArrayObject *input, *values, *signs;
    npy_intp length;
    (void)self;
    input = (PyArrayObject *)PyArray_FROM_OTF(argument, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (input == NULL) return NULL;
    values = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(input), PyArray_DIMS(input), NPY_DOUBLE);
    signs = (PyArrayObject *)PyArray_SimpleNew(PyArray_NDIM(input), PyArray_DIMS(input), NPY_INT);
    if (values == NULL || signs == NULL) {{
        Py_XDECREF(values);
        Py_XDECREF(signs);
        Py_DECREF(input);
        return PyErr_NoMemory();
    }}
    length = PyArray_SIZE(input);
    for (npy_intp i = 0; i < length; i++) {{
        int sign = 1;
        ((double *)PyArray_DATA(values))[i] =
            lgammafn_sign(((double *)PyArray_DATA(input))[i], &sign);
        ((int *)PyArray_DATA(signs))[i] = sign;
    }}
    result = PyTuple_Pack(2, (PyObject *)values, (PyObject *)signs);
    Py_DECREF(input);
    Py_DECREF(values);
    Py_DECREF(signs);
    return result;
}}

static PyObject *
py_logspace_sum_1d(PyObject *self, PyObject *argument)
{{
    PyObject *sequence;
    Py_ssize_t length;
    double *values;
    double result;
    (void)self;
    sequence = PySequence_Fast(argument, "values must be a one-dimensional sequence");
    if (sequence == NULL) return NULL;
    length = PySequence_Fast_GET_SIZE(sequence);
    if (length > INT_MAX) {{
        Py_DECREF(sequence);
        return PyErr_Format(PyExc_OverflowError, "too many values for Rmath logspace_sum");
    }}
    values = PyMem_Malloc((size_t)(length > 0 ? length : 1) * sizeof(double));
    if (values == NULL) {{
        Py_DECREF(sequence);
        return PyErr_NoMemory();
    }}
    for (Py_ssize_t i = 0; i < length; i++) {{
        values[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(sequence, i));
        if (PyErr_Occurred()) {{
            PyMem_Free(values);
            Py_DECREF(sequence);
            return NULL;
        }}
    }}
    result = logspace_sum(values, (int)length);
    PyMem_Free(values);
    Py_DECREF(sequence);
    return PyFloat_FromDouble(result);
}}

static PyObject *
py_logspace_sum_last(PyObject *self, PyObject *argument)
{{
    PyArrayObject *input, *output;
    int ndim;
    npy_intp row_length, rows;
    (void)self;
    input = (PyArrayObject *)PyArray_FROM_OTF(argument, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (input == NULL) return NULL;
    ndim = PyArray_NDIM(input);
    if (ndim == 0) {{
        Py_DECREF(input);
        return PyErr_Format(PyExc_ValueError, "logspace_sum input must have at least one dimension");
    }}
    row_length = PyArray_DIMS(input)[ndim - 1];
    if (row_length > INT_MAX) {{
        Py_DECREF(input);
        return PyErr_Format(PyExc_OverflowError, "too many values for Rmath logspace_sum");
    }}
    output = (PyArrayObject *)PyArray_SimpleNew(ndim - 1, PyArray_DIMS(input), NPY_DOUBLE);
    if (output == NULL) {{
        Py_DECREF(input);
        return NULL;
    }}
    rows = PyArray_SIZE(output);
    for (npy_intp row = 0; row < rows; row++) {{
        const double *values = ((const double *)PyArray_DATA(input)) + row * row_length;
        ((double *)PyArray_DATA(output))[row] = logspace_sum(values, (int)row_length);
    }}
    Py_DECREF(input);
    return (PyObject *)output;
}}

static PyObject *
py_rmultinom_one(PyObject *self, PyObject *args)
{{
    int size;
    PyObject *argument;
    PyObject *sequence;
    PyObject *result;
    Py_ssize_t length;
    double *probabilities;
    int *draws;
    long double total = 0.0L;
    (void)self;
    if (!PyArg_ParseTuple(args, "iO:_rmultinom_one", &size, &argument)) return NULL;
    sequence = PySequence_Fast(argument, "prob must be a one-dimensional sequence");
    if (sequence == NULL) return NULL;
    length = PySequence_Fast_GET_SIZE(sequence);
    if (length < 1 || length > INT_MAX) {{
        Py_DECREF(sequence);
        return PyErr_Format(PyExc_ValueError, "prob must contain between 1 and INT_MAX values");
    }}
    probabilities = PyMem_Malloc((size_t)length * sizeof(double));
    draws = PyMem_Malloc((size_t)length * sizeof(int));
    if (probabilities == NULL || draws == NULL) {{
        PyMem_Free(probabilities);
        PyMem_Free(draws);
        Py_DECREF(sequence);
        return PyErr_NoMemory();
    }}
    for (Py_ssize_t i = 0; i < length; i++) {{
        probabilities[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(sequence, i));
        if (PyErr_Occurred()) {{
            PyMem_Free(probabilities);
            PyMem_Free(draws);
            Py_DECREF(sequence);
            return NULL;
        }}
        total += (long double)probabilities[i];
    }}
    accudist_rng_acquire();
    rmultinom(size, probabilities, (int)length, draws);
    accudist_rng_release();
    if (fabsl(total - 1.0L) > 1e-7L) {{
        accudist_errword &= ~(unsigned)ACCUDIST_ALLOC;
        PyMem_Free(probabilities);
        PyMem_Free(draws);
        Py_DECREF(sequence);
        PyErr_SetString(PyExc_ValueError,
                        "probabilities must sum to 1 (rbinom probability sum should be 1)");
        return NULL;
    }}
    result = PyTuple_New(length);
    if (result != NULL) {{
        for (Py_ssize_t i = 0; i < length; i++) {{
            PyObject *value = PyLong_FromLong(draws[i]);
            if (value == NULL) {{
                Py_DECREF(result);
                result = NULL;
                break;
            }}
            PyTuple_SET_ITEM(result, i, value);
        }}
    }}
    PyMem_Free(probabilities);
    PyMem_Free(draws);
    Py_DECREF(sequence);
    return result;
}}

static PyObject *
py_rmultinom_rows(PyObject *self, PyObject *args)
{{
    Py_ssize_t count;
    int size;
    PyObject *argument;
    PyArrayObject *probabilities, *result;
    npy_intp dims[2], categories;
    long double total = 0.0L;
    (void)self;
    if (!PyArg_ParseTuple(args, "niO:_rmultinom_rows", &count, &size, &argument)) return NULL;
    if (count < 0) return PyErr_Format(PyExc_ValueError, "n must be non-negative");
    probabilities = (PyArrayObject *)PyArray_FROM_OTF(argument, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (probabilities == NULL) return NULL;
    if (PyArray_NDIM(probabilities) != 1 || PyArray_SIZE(probabilities) < 1 ||
        PyArray_SIZE(probabilities) > INT_MAX) {{
        Py_DECREF(probabilities);
        return PyErr_Format(PyExc_ValueError, "prob must be a non-empty one-dimensional array");
    }}
    categories = PyArray_SIZE(probabilities);
    for (npy_intp i = 0; i < categories; i++)
        total += (long double)((double *)PyArray_DATA(probabilities))[i];
    if (fabsl(total - 1.0L) > 1e-7L) {{
        Py_DECREF(probabilities);
        return PyErr_Format(PyExc_ValueError, "probabilities must sum to 1 (rbinom probability sum should be 1)");
    }}
    dims[0] = (npy_intp)count;
    dims[1] = categories;
    result = (PyArrayObject *)PyArray_SimpleNew(2, dims, NPY_INT);
    if (result == NULL) {{
        Py_DECREF(probabilities);
        return NULL;
    }}
    accudist_rng_acquire();
    for (Py_ssize_t row = 0; row < count; row++)
        rmultinom(size, (double *)PyArray_DATA(probabilities), (int)categories,
                  ((int *)PyArray_DATA(result)) + row * categories);
    accudist_rng_release();
    Py_DECREF(probabilities);
    return (PyObject *)result;
}}

static PyObject *
py_set_seed(PyObject *self, PyObject *args)
{{
    unsigned int i1, i2;
    (void)self;
    if (!PyArg_ParseTuple(args, "II:set_seed", &i1, &i2)) return NULL;
    accudist_rng_acquire();
    set_seed(i1, i2);
    accudist_rng_release();
    Py_RETURN_NONE;
}}

static PyObject *
py_get_seed(PyObject *self, PyObject *ignored)
{{
    unsigned int i1, i2;
    (void)self;
    (void)ignored;
    accudist_rng_acquire();
    get_seed(&i1, &i2);
    accudist_rng_release();
    return Py_BuildValue("(II)", i1, i2);
}}

static PyObject *
py_acquire_rng_lock(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    accudist_rng_acquire();
    Py_RETURN_NONE;
}}

static PyObject *
py_release_rng_lock(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    accudist_rng_release();
    Py_RETURN_NONE;
}}

static PyObject *
py_free_caches(PyObject *self, PyObject *ignored)
{{
    (void)self;
    (void)ignored;
    PyThread_acquire_lock(accudist_cache_lock, WAIT_LOCK);
    wilcox_free();
    signrank_free();
    PyThread_release_lock(accudist_cache_lock);
    Py_RETURN_NONE;
}}

static PyMethodDef module_methods[] = {{
    {{"_clear_error", py_clear_error, METH_NOARGS, NULL}},
    {{"_take_error", py_take_error, METH_NOARGS, NULL}},
    {{"_force_allocation_failure", py_force_allocation_failure, METH_NOARGS, NULL}},
    {{"_pnorm_both_scalar", py_pnorm_both_scalar, METH_VARARGS, NULL}},
    {{"_lgammafn_sign_scalar", py_lgammafn_sign_scalar, METH_VARARGS, NULL}},
    {{"_pnorm_both_array", py_pnorm_both_array, METH_VARARGS, NULL}},
    {{"_lgammafn_sign_array", py_lgammafn_sign_array, METH_O, NULL}},
    {{"_logspace_sum_1d", py_logspace_sum_1d, METH_O, NULL}},
    {{"_logspace_sum_last", py_logspace_sum_last, METH_O, NULL}},
    {{"_rmultinom_one", py_rmultinom_one, METH_VARARGS, NULL}},
    {{"_rmultinom_rows", py_rmultinom_rows, METH_VARARGS, NULL}},
    {{"_set_seed", py_set_seed, METH_VARARGS, NULL}},
    {{"_get_seed", py_get_seed, METH_NOARGS, NULL}},
    {{"_acquire_rng_lock", py_acquire_rng_lock, METH_NOARGS, NULL}},
    {{"_release_rng_lock", py_release_rng_lock, METH_NOARGS, NULL}},
    {{"_free_caches", py_free_caches, METH_NOARGS, NULL}},
    {{NULL, NULL, 0, NULL}}
}};

static void
module_free(void *module)
{{
    (void)module;
    if (accudist_cache_lock != NULL) {{
        PyThread_acquire_lock(accudist_cache_lock, WAIT_LOCK);
        wilcox_free();
        signrank_free();
        PyThread_release_lock(accudist_cache_lock);
    }}
    accudist_free_locks();
}}

static struct PyModuleDef module_def = {{
    PyModuleDef_HEAD_INIT,
    "_ufuncs",
    "Generated NumPy ufuncs backed by R nmath.",
    -1,
    module_methods,
    NULL,
    NULL,
    NULL,
    module_free
}};

PyMODINIT_FUNC
PyInit__ufuncs(void)
{{
    PyObject *module;
    import_array();
    import_umath();
    if (accudist_init_locks() < 0) {{
        PyErr_NoMemory();
        return NULL;
    }}
    module = PyModule_Create(&module_def);
    if (module == NULL) {{
        accudist_free_locks();
        return NULL;
    }}
#ifdef Py_GIL_DISABLED
    if (PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED) < 0) {{
        Py_DECREF(module);
        return NULL;
    }}
#endif
{chr(10).join(registrations)}
    return module;
}}
"""


def parameter_list(
    function: dict, *, typed: bool = False, documentation: bool = False
) -> list[str]:
    params: list[str] = []
    for param in function["params"]:
        name = param["py"]
        if function.get("alias") == "rate_scale":
            if name == "rate":
                default = (
                    repr(param["default"])
                    if typed or documentation
                    else "_dispatch.DEFAULT_RATE"
                )
            elif name == "scale":
                default = "None"
            else:
                default = repr(param["default"]) if "default" in param else None
        elif function.get("dispatch") == "prob_or_mu" and name in {"prob", "mu"}:
            default = "None"
        elif "default" in param:
            default = repr(param["default"])
        else:
            default = None
        annotation = ": Any" if typed else ""
        suffix = f" = {default}" if typed and default is not None else (
            f"={default}" if default is not None else ""
        )
        params.append(f"{name}{annotation}{suffix}")
    if function.get("dispatch") == "ncp":
        params.append("ncp: Any = None" if typed else "ncp=None")
    for flag in function["flags"]:
        default = "True" if flag == "lower_tail" else "False"
        params.append(f"{flag}: bool = {default}" if typed else f"{flag}={default}")
    if function["kind"] != "r":
        params.append("out: Any = None" if typed else "out=None")
    return params


def python_call_args(function: dict, call: dict) -> list[str]:
    if function["kind"] in {"d", "p", "q"}:
        args = [function["params"][0]["py"], *call["c_args"]]
    else:
        args = list(call["c_args"])
    args.extend(f"int({flag})" for flag in function["flags"])
    return args


def raw_expression(function: dict, call: dict, *, indent: str) -> str:
    symbol = call["c_symbol"]
    args = python_call_args(function, call)
    if function["kind"] == "r":
        count = function["params"][0]["py"]
        return f"{indent}result = _rng.draw(_ufuncs.{symbol}, {count}, {', '.join(call['c_args'])})"
    return f"{indent}result = _ufuncs.{symbol}({', '.join(args)}, out=out)"


def render_wrapper(function: dict) -> str:
    name = function["name"]
    lines = [
        f"def {name}({', '.join(parameter_list(function))}):",
    ]
    summary = function.get("summary", name + " backed by R 4.5.2 nmath")
    if function.get("r_equivalent"):
        summary += f" R: {function['r_equivalent']}"
    if function["kind"] == "r":
        summary += "; does not reproduce R's set.seed() stream"
    lines.append(f'    """{summary}."""')
    if function.get("alias") == "rate_scale":
        lines.append("    scale = _dispatch.resolve_rate_scale(rate, scale)")
    for target, expression in function.get("c_transform", {}).items():
        if expression == "1.0 / rate":
            lines.append(f"    {target} = _dispatch.reciprocal({target})")
        elif expression == "2.0 if expon_scaled else 1.0":
            lines.append(f"    {target} = 2.0 if {target} else 1.0")
        else:
            raise ValueError(f"unsupported transform for {name}: {expression}")

    if function["kind"] == "r" and function.get("dispatch") == "ncp" and "composed" in function.get("call_ncp", {}):
        central = function["call"]
        lines.append("    if ncp is not None:")
        lines.append("        with _errstate.suppress_numpy_warnings(), _rng.locked():")
        if name == "rbeta":
            lines.extend([
                "            x = rchisq(n, 2 * shape1, ncp=ncp)",
                "            return x / (x + rchisq(n, 2 * shape2))",
            ])
        elif name == "rf":
            lines.append("            return (rchisq(n, df1, ncp=ncp) / df1) / (rchisq(n, df2) / df2)")
        elif name == "rt":
            lines.append("            return rnorm(n, ncp) / _dispatch.sqrt(rchisq(n, df) / df)")
        else:
            raise ValueError(f"unsupported composed RNG {name}")
        lines.append(f"    with _errstate.suppress_numpy_warnings(), _errstate.capture(\"{name}\") as _capture:")
        lines.append(raw_expression(function, central, indent="        "))
    else:
        lines.append(f"    with _errstate.suppress_numpy_warnings(), _errstate.capture(\"{name}\") as _capture:")
        dispatch = function.get("dispatch")
        if dispatch == "ncp":
            lines.append("        if ncp is None:")
            lines.append(raw_expression(function, function["call"], indent="            "))
            lines.append("        else:")
            lines.append(raw_expression(function, function["call_ncp"], indent="            "))
        elif dispatch == "prob_or_mu":
            lines.append("        parameterization = _dispatch.resolve_prob_mu(prob, mu)")
            lines.append("        if parameterization == 'prob':")
            lines.append(raw_expression(function, function["call"], indent="            "))
            lines.append("        else:")
            lines.append(raw_expression(function, function["call_mu"], indent="            "))
        else:
            lines.append(raw_expression(function, function["call"], indent="        "))
    lines.extend(["    _capture.check()", "    return result", ""])
    return "\n".join(lines)


def render_api(functions: list[dict]) -> str:
    pieces = [
        "# GENERATED by tools/regen.py -- do not edit.\n",
        "from __future__ import annotations\n\n",
        "from . import _dispatch, _errstate, _rng, _ufuncs\n\n",
    ]
    pieces.extend(render_wrapper(function) + "\n" for function in functions)
    names = [function["name"] for function in functions]
    pieces.append(f"__all__ = {names!r}\n")
    return "".join(pieces)


def render_stub(functions: list[dict]) -> str:
    lines = [
        "# GENERATED by tools/regen.py -- do not edit.\n",
        "from typing import Any\n",
        "import numpy as np\n\n",
    ]
    for function in functions:
        return_type = "np.ndarray[Any, Any]" if function["kind"] == "r" else "np.float64 | np.ndarray[Any, Any]"
        lines.append(
            f"def {function['name']}({', '.join(parameter_list(function, typed=True))}) -> {return_type}: ...\n"
        )
    return "".join(lines)


def render_rmath(functions: list[dict]) -> str:
    names = list(ufunc_specs(functions))
    lines = [
        "# GENERATED by tools/regen.py -- do not edit.\n",
        '"""Raw, positional, one-to-one mappings to Rmath.h."""\n',
        "from . import _ufuncs\n\n",
    ]
    lines.extend(f"{name} = _ufuncs.{name}\n" for name in names)
    lines.append(f"\n__all__ = {names!r}\n")
    return "".join(lines)


def render_manifest_test(functions: list[dict]) -> str:
    names = [function["name"] for function in functions]
    return f'''# GENERATED by tools/regen.py -- do not edit.
import pytest
import accudist as ad


@pytest.mark.parametrize("name", {names!r})
def test_manifest_function_is_public(name):
    assert callable(getattr(ad, name))
    assert name in ad.__all__
'''


def render_api_reference(functions: list[dict], bespoke: list[dict]) -> str:
    """Render the public function inventory from the canonical manifest."""

    labels = {
        "d": "Densities and probability masses",
        "p": "Distribution functions",
        "q": "Quantiles",
        "r": "Random variates",
        "special": "Special functions",
        "util": "Utilities",
    }
    lines = [
        "<!-- GENERATED by tools/regen.py -- do not edit. -->",
        "# API reference",
        "",
        "This page is generated from `docs/functions.toml`, the canonical public",
        "function inventory. All numerical arguments accept NumPy-broadcastable",
        "array-like values. Non-random functions return `numpy.float64` for scalar",
        "inputs and arrays otherwise; `out=` accepts a compatible NumPy output array.",
        "",
        "For every probability and quantile function, `lower_tail=False` selects",
        "R's directly computed upper tail. `log=True` selects natural-log results",
        "or inputs, exactly as it does in the corresponding R function.",
        "",
    ]
    for kind in ("d", "p", "q", "r", "special", "util"):
        members = [function for function in functions if function["kind"] == kind]
        lines.extend(
            [
                f"## {labels[kind]}",
                "",
                "| Function | Signature | R help topic |",
                "|---|---|---|",
            ]
        )
        for function in members:
            name = function["name"]
            signature = f"{name}({', '.join(parameter_list(function, documentation=True))})"
            topic = function.get("r_page", "—")
            lines.append(f"| `{name}` | `{signature}` | {topic} |")
        lines.append("")
    lines.extend(
        [
            "## Array and multi-output functions",
            "",
            "These functions need hand-written wrappers rather than scalar NumPy",
            "ufuncs, but remain part of the public numerical API.",
            "",
            "| Function | Interface reason |",
            "|---|---|",
        ]
    )
    for function in bespoke:
        lines.append(f"| `{function['name']}` | {function['reason']} |")
    lines.extend(
        [
            "",
            "## Package services",
            "",
            "| Public name | Purpose |",
            "|---|---|",
            "| `errstate` | Thread-local numerical error policy context manager/decorator. |",
            "| `AccudistWarning` | Base numerical warning class. |",
            "| `AccudistDomainWarning` | Domain warning. |",
            "| `AccudistRangeWarning` | Range warning. |",
            "| `AccudistConvergenceWarning` | Convergence warning. |",
            "| `AccudistPrecisionWarning` | Precision warning. |",
            "| `AccudistUnderflowWarning` | Underflow warning. |",
            "| `AccudistDomainError` | Raised domain error. |",
            "| `AccudistRangeError` | Raised range error. |",
            "| `AccudistConvergenceError` | Raised convergence error. |",
            "| `AccudistPrecisionError` | Raised precision error. |",
            "| `AccudistUnderflowError` | Raised underflow error. |",
            "| `RNG` | Independent deterministic standalone-Rmath stream. |",
            "| `default_rng` | Return the process-default accudist stream. |",
            "| `set_seed` | Set the two-word seed of the default stream. |",
            "| `get_seed` | Return the two-word seed of the default stream. |",
            "| `free_caches` | Release Wilcoxon and sign-rank work caches. |",
            "",
            "See [numerical errors](errors.md) and [random numbers](rng.md) for",
            "usage and behavioral details.",
            "",
        ]
    )
    return "\n".join(lines)


def render_all(manifest: Path) -> dict[str, str]:
    data = tomllib.loads(manifest.read_text())
    functions = enabled_functions(data)
    return {
        "_ufuncs.c": render_c(functions),
        "_api.py": render_api(functions),
        "_generated.pyi": render_stub(functions),
        "rmath.py": render_rmath(functions),
        "test_manifest.py": render_manifest_test(functions),
        "api-reference.md": render_api_reference(functions, data["bespoke"]),
    }


def write_outputs(outputs: dict[str, str], output_dir: Path, build_mode: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        if build_mode and name not in BUILD_GENERATED:
            continue
        target = output_dir / name if build_mode else GENERATED[name]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def check_outputs(outputs: dict[str, str]) -> int:
    failed = False
    for name, content in outputs.items():
        target = GENERATED[name]
        actual = target.read_text() if target.exists() else ""
        if actual == content:
            continue
        failed = True
        print(f"stale generated file: {target.relative_to(ROOT)}")
        print("".join(difflib.unified_diff(actual.splitlines(True), content.splitlines(True))))
    return int(failed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("output_dir", nargs="?", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render_all(args.manifest)
    if args.check:
        raise SystemExit(check_outputs(outputs))
    output_dir = args.output_dir or ROOT / "accudist"
    write_outputs(outputs, output_dir, build_mode=args.output_dir is not None)


if __name__ == "__main__":
    main()
