#if defined(__APPLE__)
#include <mach/mach.h>
#include <mach/mach_time.h>
#elif _WIN32
#include <time.h>
#include <windows.h>
#else
#include <sys/time.h>
#endif

#include <stdint.h>

#include "cycletimer.h"

uint64_t currentTicks() {
#if defined(__APPLE__)
    return mach_absolute_time();
#elif defined(_WIN32)
    LARGE_INTEGER qwTime;
    QueryPerformanceCounter(&qwTime);
    return qwTime.QuadPart;
#elif defined(__x86_64__)
    unsigned int a, d;
    asm volatile("rdtsc" : "=a"(a), "=d"(d));
    return ((uint64_t)d << 32) + a;
#else
    timespec spec;
    clock_gettime(CLOCK_THREAD_CPUTIME_ID, &spec);
    return spec.tv_sec * 1000 * 1000 * 1000 + spec.tv_nsec;
#endif
}
