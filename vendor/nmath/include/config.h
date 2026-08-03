/* Standalone nmath feature checks for supported C11 toolchains. */
#ifndef ACCUDIST_CONFIG_H
#define ACCUDIST_CONFIG_H
#include <stdbool.h>
#define HAVE_LONG_DOUBLE 1
#define HAVE_NEARBYINT 1
#define HAVE_WORKING_ISFINITE 1
#if defined(__APPLE__)
# define HAVE___COSPI 1
# define HAVE___SINPI 1
# define HAVE___TANPI 1
#endif
#endif
