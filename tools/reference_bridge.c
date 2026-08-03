#include <R.h>
#include <Rinternals.h>
#include <Rmath.h>
#include <limits.h>

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

SEXP accudist_ref_lgammafn_sign(SEXP x)
{
    int sign = 1;
    double value = lgammafn_sign(asReal(x), &sign);
    SEXP result = PROTECT(allocVector(REALSXP, 2));
    REAL(result)[0] = value;
    REAL(result)[1] = (double)sign;
    UNPROTECT(1);
    return result;
}

SEXP accudist_ref_logspace_sum(SEXP values)
{
    SEXP numeric = PROTECT(coerceVector(values, REALSXP));
    R_xlen_t length = XLENGTH(numeric);
    if (length > INT_MAX) error("too many values for logspace_sum");
    double result = logspace_sum(REAL(numeric), (int)length);
    UNPROTECT(1);
    return ScalarReal(result);
}
