#ifndef ACCUDIST_SHIM_H
#define ACCUDIST_SHIM_H

#if defined(_MSC_VER)
#  define ACCUDIST_THREAD_LOCAL __declspec(thread)
#else
#  define ACCUDIST_THREAD_LOCAL _Thread_local
#endif

typedef enum {
    ACCUDIST_OK        = 0,
    ACCUDIST_DOMAIN    = 1u << 0,
    ACCUDIST_RANGE     = 1u << 1,
    ACCUDIST_NOCONV    = 1u << 2,
    ACCUDIST_PRECISION = 1u << 3,
    ACCUDIST_UNDERFLOW = 1u << 4,
    ACCUDIST_ALLOC     = 1u << 5
} accudist_flag;

extern ACCUDIST_THREAD_LOCAL unsigned accudist_errword;
#define accudist_set_flag(f) \
    (accudist_errword |= (unsigned)(f))

void accudist_warn(const char *format, ...);
void accudist_fatal(const char *format, ...);
unsigned accudist_take_error(void);
void accudist_clear_error(void);
int accudist_init_locks(void);
void accudist_free_locks(void);
void accudist_rng_acquire(void);
void accudist_rng_release(void);

#endif
