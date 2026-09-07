#include "accudist_shim.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

ACCUDIST_TLS unsigned accudist_errword = 0;
ACCUDIST_TLS char accudist_errmsg[ACCUDIST_ERRMSG_LEN] = "";
ACCUDIST_TLS int accudist_fail_calloc_after = -1;

static void record_message(const char *fmt, va_list ap)
{
    /* keep the first message of a call; later ones are usually repeats */
    if (accudist_errmsg[0] != '\0')
        return;
    vsnprintf(accudist_errmsg, ACCUDIST_ERRMSG_LEN, fmt, ap);
    /* nmath messages end in '\n'; strip it */
    size_t n = strlen(accudist_errmsg);
    while (n > 0 && (accudist_errmsg[n - 1] == '\n' || accudist_errmsg[n - 1] == ' '))
        accudist_errmsg[--n] = '\0';
}

void accudist_warning(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    record_message(fmt, ap);
    va_end(ap);
    accudist_errword |= ACCUDIST_MESSAGE;
}

void accudist_fatal(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    record_message(fmt, ap);
    va_end(ap);
    accudist_errword |= ACCUDIST_ALLOC;
}

/* calloc wrapper.  When accudist_fail_calloc_after >= 0 the counter is
   decremented on every call and the allocation fails once it reaches zero.
   This exists solely so the test-suite can prove that an allocation failure
   raises MemoryError instead of killing the interpreter. */
void *accudist_calloc(size_t nmemb, size_t size)
{
    if (accudist_fail_calloc_after >= 0) {
        if (accudist_fail_calloc_after == 0) {
            accudist_fail_calloc_after = -1;
            return NULL;
        }
        accudist_fail_calloc_after--;
    }
    return calloc(nmemb, size);
}

void accudist_clear(void)
{
    accudist_errword = 0;
    accudist_errmsg[0] = '\0';
}

unsigned accudist_flags(void)
{
    return accudist_errword;
}

const char *accudist_message(void)
{
    return accudist_errmsg;
}
