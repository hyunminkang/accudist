/* accudist: minimal stand-in for R's configure-generated config.h.
   Only the macros nmath consults when built with -DMATHLIB_STANDALONE. */
#ifndef ACCUDIST_CONFIG_H
#define ACCUDIST_CONFIG_H

#define IEEE_754 1

/* HAVE_LONG_DOUBLE is deliberately NOT defined, so nmath's LDOUBLE is plain
   double (R's own `--disable-long-double` configuration, and what R already
   uses on Apple silicon and Windows/MSVC, where long double == double).
   With platform long double, the non-central beta/chi-squared/t/F tails differ
   between x86_64 (80-bit), aarch64 Linux (128-bit) and the double platforms by
   far more than the last few bits; with plain double every accudist wheel
   returns the same numbers, and they match the reference values from R. */
#define HAVE_NEARBYINT 1
#define HAVE_WORKING_ISFINITE 1
#define HAVE_EXPM1 1
#define HAVE_HYPOT 1
#define HAVE_LOG1P 1
#define HAVE_WORKING_LOG1P 1

/* hide nmath's internal symbols from the extension module's export table */
#if defined(__GNUC__) || defined(__clang__)
# define HAVE_VISIBILITY_ATTRIBUTE 1
#endif

#endif /* ACCUDIST_CONFIG_H */
