#ifndef COLLAR_SUPERVISOR_H
#define COLLAR_SUPERVISOR_H
#include "recovery.h"
#include <zephyr/toolchain.h>

int supervisor_init(uint32_t *reset_cause);
void supervisor_enter(enum tracker_phase phase, uint32_t budget_ms);
FUNC_NORETURN void supervisor_reset(const char *reason);
FUNC_NORETURN void supervisor_service_hold(const char *reason);
void supervisor_sleep(uint32_t duration_ms);

#endif
