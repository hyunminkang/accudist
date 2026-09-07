/* accudist._ufuncs -- the C extension module.
 *
 * Hand-written part: module init, RNG state access, the bespoke (non-ufunc)
 * entry points, error-word access for the Python wrapper.  The one-ufunc-per-
 * Rmath-symbol table lives in _ufuncs_generated.c (produced by tools/regen.py).
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#define NPY_NO_DEPRECATED_API NPY_1_25_API_VERSION
/* this file owns the NumPy C-API tables; _ufuncs_generated.c shares them */
#define PY_ARRAY_UNIQUE_SYMBOL accudist_ARRAY_API
#define PY_UFUNC_UNIQUE_SYMBOL accudist_UFUNC_API
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>
#include <fenv.h>

#include <Rmath.h>
#include "accudist_shim.h"

int accudist_add_generated_ufuncs(PyObject *m);

/* ---- error word ------------------------------------------------------- */

static PyObject *py_clear_error(PyObject *self, PyObject *noargs)
{
    accudist_clear();
    Py_RETURN_NONE;
}

static PyObject *py_take_error(PyObject *self, PyObject *noargs)
{
    unsigned flags = accudist_flags();
    const char *msg = accudist_message();
    PyObject *res = Py_BuildValue("(Is)", flags, msg);
    accudist_clear();
    return res;
}

static PyObject *py_set_fail_calloc_after(PyObject *self, PyObject *arg)
{
    long k = PyLong_AsLong(arg);
    if (k == -1 && PyErr_Occurred())
        return NULL;
    accudist_fail_calloc_after = (int)k;
    Py_RETURN_NONE;
}

/* ---- caches ----------------------------------------------------------- */

static PyObject *py_free_caches(PyObject *self, PyObject *noargs)
{
    wilcox_free();
    signrank_free();
    Py_RETURN_NONE;
}

/* ---- RNG state -------------------------------------------------------- */

static PyObject *py_set_seed(PyObject *self, PyObject *args)
{
    unsigned int i1, i2;
    if (!PyArg_ParseTuple(args, "II", &i1, &i2))
        return NULL;
    set_seed(i1, i2);
    Py_RETURN_NONE;
}

static PyObject *py_get_seed(PyObject *self, PyObject *noargs)
{
    unsigned int i1, i2;
    get_seed(&i1, &i2);
    return Py_BuildValue("(II)", i1, i2);
}

typedef double (*draw0_fn)(void);

static PyObject *draw_n(PyObject *arg, draw0_fn fn)
{
    Py_ssize_t n = PyLong_AsSsize_t(arg);
    if (n == -1 && PyErr_Occurred())
        return NULL;
    if (n < 0) {
        PyErr_SetString(PyExc_ValueError, "n must be non-negative");
        return NULL;
    }
    npy_intp dims[1] = {(npy_intp)n};
    PyArrayObject *out = (PyArrayObject *)PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    if (!out)
        return NULL;
    double *p = (double *)PyArray_DATA(out);
    for (Py_ssize_t i = 0; i < n; i++)
        p[i] = fn();
    return (PyObject *)out;
}

static PyObject *py_unif_rand(PyObject *self, PyObject *arg) { return draw_n(arg, unif_rand); }
static PyObject *py_norm_rand(PyObject *self, PyObject *arg) { return draw_n(arg, norm_rand); }
static PyObject *py_exp_rand(PyObject *self, PyObject *arg)  { return draw_n(arg, exp_rand); }

/* rmultinom(size, prob, n) -> int32 array of shape (n, K) */
static PyObject *py_rmultinom(PyObject *self, PyObject *args)
{
    int size;
    PyObject *prob_obj;
    Py_ssize_t n;
    if (!PyArg_ParseTuple(args, "iOn", &size, &prob_obj, &n))
        return NULL;
    if (n < 0) {
        PyErr_SetString(PyExc_ValueError, "n must be non-negative");
        return NULL;
    }
    PyArrayObject *prob = (PyArrayObject *)PyArray_FROM_OTF(prob_obj, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (!prob)
        return NULL;
    if (PyArray_NDIM(prob) != 1) {
        Py_DECREF(prob);
        PyErr_SetString(PyExc_ValueError, "prob must be one-dimensional");
        return NULL;
    }
    npy_intp K = PyArray_DIM(prob, 0);
    if (K > INT_MAX) {
        Py_DECREF(prob);
        PyErr_SetString(PyExc_ValueError, "prob is too long");
        return NULL;
    }
    npy_intp dims[2] = {(npy_intp)n, K};
    PyArrayObject *out = (PyArrayObject *)PyArray_ZEROS(2, dims, NPY_INT, 0);
    if (!out) {
        Py_DECREF(prob);
        return NULL;
    }
    double *pp = (double *)PyArray_DATA(prob);
    int *po = (int *)PyArray_DATA(out);
    for (Py_ssize_t i = 0; i < n; i++) {
        rmultinom(size, pp, (int)K, po + i * K);
        if (accudist_flags() & ACCUDIST_ALLOC)
            break;  /* invalid prob: message recorded, wrapper raises */
    }
    Py_DECREF(prob);
    return (PyObject *)out;
}

/* logspace_sum(x) for a C-contiguous 2-D array of shape (m, k) -> (m,) */
static PyObject *py_logspace_sum(PyObject *self, PyObject *arg)
{
    PyArrayObject *x = (PyArrayObject *)PyArray_FROM_OTF(arg, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
    if (!x)
        return NULL;
    if (PyArray_NDIM(x) != 2) {
        Py_DECREF(x);
        PyErr_SetString(PyExc_ValueError, "expected a 2-D array");
        return NULL;
    }
    npy_intp m = PyArray_DIM(x, 0), k = PyArray_DIM(x, 1);
    if (k > INT_MAX) {
        Py_DECREF(x);
        PyErr_SetString(PyExc_ValueError, "last axis is too long");
        return NULL;
    }
    npy_intp dims[1] = {m};
    PyArrayObject *out = (PyArrayObject *)PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    if (!out) {
        Py_DECREF(x);
        return NULL;
    }
    double *px = (double *)PyArray_DATA(x), *po = (double *)PyArray_DATA(out);
    for (npy_intp i = 0; i < m; i++)
        po[i] = logspace_sum(px + i * k, (int)k);
    Py_DECREF(x);
    return (PyObject *)out;
}

/* ---- bespoke two-output ufuncs --------------------------------------- */

static void pnorm_both_loop(char **args, npy_intp const *dims, npy_intp const *steps, void *data)
{
    npy_intp n = dims[0];
    char *ix = args[0], *ilog = args[1], *olo = args[2], *oup = args[3];
    for (npy_intp i = 0; i < n; i++) {
        double lo, up;
        pnorm_both(*(double *)ix, &lo, &up, 2, (int)(*(double *)ilog != 0.0));
        *(double *)olo = lo;
        *(double *)oup = up;
        ix += steps[0]; ilog += steps[1]; olo += steps[2]; oup += steps[3];
    }
    feclearexcept(FE_ALL_EXCEPT);
}

static void lgammafn_sign_loop(char **args, npy_intp const *dims, npy_intp const *steps, void *data)
{
    npy_intp n = dims[0];
    char *ix = args[0], *ov = args[1], *os = args[2];
    for (npy_intp i = 0; i < n; i++) {
        int sgn = 1;
        *(double *)ov = lgammafn_sign(*(double *)ix, &sgn);
        *(double *)os = (double)sgn;
        ix += steps[0]; ov += steps[1]; os += steps[2];
    }
    feclearexcept(FE_ALL_EXCEPT);
}

static PyUFuncGenericFunction pnorm_both_funcs[1] = {&pnorm_both_loop};
static char pnorm_both_types[4] = {NPY_DOUBLE, NPY_DOUBLE, NPY_DOUBLE, NPY_DOUBLE};
static PyUFuncGenericFunction lgammafn_sign_funcs[1] = {&lgammafn_sign_loop};
static char lgammafn_sign_types[3] = {NPY_DOUBLE, NPY_DOUBLE, NPY_DOUBLE};
static void *bespoke_data[1] = {NULL};

static int add_bespoke_ufuncs(PyObject *m)
{
    PyObject *f;
    f = PyUFunc_FromFuncAndData(pnorm_both_funcs, bespoke_data, pnorm_both_types, 1, 2, 2,
                                PyUFunc_None, "pnorm_both",
                                "pnorm_both(x, log_p) -> (lower, upper)  [C: pnorm_both(x, &cum, &ccum, 2, log_p)]", 0);
    if (!f || PyModule_AddObject(m, "pnorm_both", f) < 0) {
        Py_XDECREF(f);
        return -1;
    }
    f = PyUFunc_FromFuncAndData(lgammafn_sign_funcs, bespoke_data, lgammafn_sign_types, 1, 1, 2,
                                PyUFunc_None, "lgammafn_sign",
                                "lgammafn_sign(x) -> (lgamma, sign)  [C: lgammafn_sign(x, &sgn)]", 0);
    if (!f || PyModule_AddObject(m, "lgammafn_sign", f) < 0) {
        Py_XDECREF(f);
        return -1;
    }
    return 0;
}

/* ---- module ------------------------------------------------------------ */

static PyMethodDef methods[] = {
    {"_clear_error", py_clear_error, METH_NOARGS, "reset the thread-local error word"},
    {"_take_error", py_take_error, METH_NOARGS, "return (flags, message) and reset"},
    {"_set_fail_calloc_after", py_set_fail_calloc_after, METH_O, "test hook: make the k-th next calloc fail"},
    {"free_caches", py_free_caches, METH_NOARGS, "free the wilcox/signrank distribution tables"},
    {"set_seed", py_set_seed, METH_VARARGS, "set_seed(i1, i2): install the global RNG state"},
    {"get_seed", py_get_seed, METH_NOARGS, "get_seed() -> (i1, i2)"},
    {"unif_rand", py_unif_rand, METH_O, "unif_rand(n) -> n uniforms on [0,1)"},
    {"norm_rand", py_norm_rand, METH_O, "norm_rand(n) -> n standard normals"},
    {"exp_rand", py_exp_rand, METH_O, "exp_rand(n) -> n standard exponentials"},
    {"rmultinom", py_rmultinom, METH_VARARGS, "rmultinom(size, prob, n) -> (n, K) int array"},
    {"logspace_sum", py_logspace_sum, METH_O, "logspace_sum(x2d) -> log(sum(exp(x))) along axis 1"},
    {NULL, NULL, 0, NULL},
};

static void module_free(void *m)
{
    wilcox_free();
    signrank_free();
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT, "accudist._ufuncs",
    "Raw NumPy ufuncs over R's nmath library (one per Rmath.h symbol).",
    -1, methods, NULL, NULL, NULL, module_free,
};

PyMODINIT_FUNC PyInit__ufuncs(void)
{
    import_array();
    import_umath();
    PyObject *m = PyModule_Create(&moduledef);
    if (!m)
        return NULL;
    if (PyModule_AddStringConstant(m, "R_VERSION", R_VERSION_STRING) < 0)
        goto fail;
    if (PyModule_AddIntConstant(m, "FLAG_ALLOC", ACCUDIST_ALLOC) < 0 ||
        PyModule_AddIntConstant(m, "FLAG_MESSAGE", ACCUDIST_MESSAGE) < 0 ||
        PyModule_AddIntConstant(m, "WILCOX_MAX", 50) < 0)
        goto fail;
    if (accudist_add_generated_ufuncs(m) < 0 || add_bespoke_ufuncs(m) < 0)
        goto fail;
    return m;
fail:
    Py_DECREF(m);
    return NULL;
}
