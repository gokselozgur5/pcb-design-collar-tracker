#ifndef COLLAR_HOST_WATCHDOG_H
#define COLLAR_HOST_WATCHDOG_H
#include <zephyr/device.h>
#include <stdint.h>
#define WDT_FLAG_RESET_SOC 1
struct wdt_timeout_cfg { uint32_t flags; struct { uint32_t min, max; } window; };
int wdt_install_timeout(const struct device *, const struct wdt_timeout_cfg *);
int wdt_setup(const struct device *, uint8_t);
int wdt_feed(const struct device *, int);
#endif
