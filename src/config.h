/* accudist: minimal stand-in for R's configure-generated config.h.
   Only the macros nmath consults when built with -DMATHLIB_STANDALONE. */
#ifndef ACCUDIST_CONFIG_H
#define ACCUDIST_CONFIG_H

#define IEEE_754 1
#define HAVE_LONG_DOUBLE 1
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
