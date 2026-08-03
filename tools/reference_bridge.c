#include <R.h>
#include <Rinternals.h>
#include <Rmath.h>

#define UNARY_WRAPPER(py_name, c_name) \
    SEXP py_name(SEXP x) { return ScalarReal(c_name(asReal(x))); }
#define BINARY_WRAPPER(py_name, c_name) \
    SEXP py_name(SEXP x, SEXP y) { return ScalarReal(c_name(asReal(x), asReal(y))); }

UNARY_WRAPPER(accudist_ref_log1pmx, log1pmx)
UNARY_WRAPPER(accudist_ref_log1pexp, log1pexp)
UNARY_WRAPPER(accudist_ref_lgamma1p, lgamma1p)
UNARY_WRAPPER(accudist_ref_ftrunc, ftrunc)
UNARY_WRAPPER(accudist_ref_tanpi, tanpi)
BINARY_WRAPPER(accudist_ref_logspace_add, logspace_add)
BINARY_WRAPPER(accudist_ref_logspace_sub, logspace_sub)
BINARY_WRAPPER(accudist_ref_fprec, fprec)
BINARY_WRAPPER(accudist_ref_fround, fround)
BINARY_WRAPPER(accudist_ref_fsign, fsign)
