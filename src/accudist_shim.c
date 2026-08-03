#include <Python.h>

#include "accudist_shim.h"

ACCUDIST_THREAD_LOCAL unsigned accudist_errword = ACCUDIST_OK;
ACCUDIST_THREAD_LOCAL jmp_buf *accudist_jump_target = NULL;
PyThread_type_lock accudist_cache_lock = NULL;
PyThread_type_lock accudist_rng_lock = NULL;

void
accudist_warn(const char *format, ...)
{
    (void)format;
    accudist_set_flag(ACCUDIST_RANGE);
}

void
accudist_fatal(const char *format, ...)
{
    (void)format;
    accudist_set_flag(ACCUDIST_ALLOC);
    if (accudist_jump_target != NULL) {
        longjmp(*accudist_jump_target, 1);
    }
}

unsigned
accudist_take_error(void)
{
    unsigned result = accudist_errword;
    accudist_errword = ACCUDIST_OK;
    return result;
}

void
accudist_clear_error(void)
{
    accudist_errword = ACCUDIST_OK;
}

int
accudist_init_locks(void)
{
    accudist_cache_lock = PyThread_allocate_lock();
    if (accudist_cache_lock == NULL) {
        return -1;
    }
    accudist_rng_lock = PyThread_allocate_lock();
    if (accudist_rng_lock == NULL) {
        PyThread_free_lock(accudist_cache_lock);
        accudist_cache_lock = NULL;
        return -1;
    }
    return 0;
}

void
accudist_free_locks(void)
{
    if (accudist_cache_lock != NULL) {
        PyThread_free_lock(accudist_cache_lock);
        accudist_cache_lock = NULL;
    }
    if (accudist_rng_lock != NULL) {
        PyThread_free_lock(accudist_rng_lock);
        accudist_rng_lock = NULL;
    }
}
