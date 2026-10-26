#ifndef COLLAR_HOST_DEVICE_H
#define COLLAR_HOST_DEVICE_H
#include <stdbool.h>
struct device { int unused; };
extern const struct device test_watchdog_device;
bool device_is_ready(const struct device *);
#define DT_NODELABEL(name) 0
#define DEVICE_DT_GET(node) (&test_watchdog_device)
#endif
