/* accudist: minimal stand-in for R's configure-generated Rconfig.h. */
#ifndef ACCUDIST_RCONFIG_H
#define ACCUDIST_RCONFIG_H

#define IEEE_754 1
#define HAVE_UINTPTR_T 1
#if defined(__GNUC__) || defined(__clang__)
# define HAVE_VISIBILITY_ATTRIBUTE 1
#endif

#endif /* ACCUDIST_RCONFIG_H */
