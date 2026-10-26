#ifndef COLLAR_TRIAL_HOST_KERNEL_H
#define COLLAR_TRIAL_HOST_KERNEL_H
/* Keep POSIX scheduling, but advance the trial clock without waiting ten minutes. */
#define k_uptime_get host_real_uptime_get
#include "../../../../tracker-r02/tests/host/zephyr/kernel.h"
#undef k_uptime_get
extern atomic_llong trial_test_now;
static inline int64_t k_uptime_get(void) { return atomic_load(&trial_test_now); }
#endif
