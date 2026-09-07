/* accudist shim: the only code that sits between nmath and Python.
 *
 * nmath (built standalone) reports trouble by printing to stdout and, on
 * allocation failure, calling exit(1).  Patch 0001 redirects every such macro
 * here.  We record the event in a thread-local flag word plus a small message
 * buffer, return, and let the Python wrapper decide whether to warn or raise.
 */
#ifndef ACCUDIST_SHIM_H
#define ACCUDIST_SHIM_H

#include <stddef.h>

#if defined(_MSC_VER)
# define ACCUDIST_TLS __declspec(thread)
#else
# define ACCUDIST_TLS _Thread_local
#endif

/* Bits 1..16 are nmath's own ME_DOMAIN, ME_RANGE, ME_NOCONV, ME_PRECISION,
   ME_UNDERFLOW codes, stored verbatim.  The two below are accudist's. */
#define ACCUDIST_ALLOC    32u  /* MATHLIB_ERROR fired (allocation failure / fatal) */
#define ACCUDIST_MESSAGE  64u  /* MATHLIB_WARNING fired; text in accudist_errmsg */

#define ACCUDIST_ERRMSG_LEN 256

extern ACCUDIST_TLS unsigned accudist_errword;
extern ACCUDIST_TLS char accudist_errmsg[ACCUDIST_ERRMSG_LEN];
extern ACCUDIST_TLS int accudist_fail_calloc_after;  /* test hook, see accudist_calloc */

#define accudist_set_flag(f) (accudist_errword |= (unsigned)(f))

void accudist_warning(const char *fmt, ...);
void accudist_fatal(const char *fmt, ...);
void *accudist_calloc(size_t nmemb, size_t size);

/* clear and read back, used once per Python-level call */
void accudist_clear(void);
unsigned accudist_flags(void);
const char *accudist_message(void);

#endif /* ACCUDIST_SHIM_H */
