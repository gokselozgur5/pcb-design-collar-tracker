#include "supervisor.h"
#include <modem/nrf_modem_lib.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>
#include <assert.h>
#include <errno.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

const struct device test_watchdog_device = {0};
static atomic_int feeds, returned;
static bool ready = true;
static unsigned installations, starts, cleared;
bool device_is_ready(const struct device *dev) { assert(dev == &test_watchdog_device); return ready; }
int hwinfo_get_reset_cause(uint32_t *cause) { *cause = 0x1234; return 0; }
int hwinfo_clear_reset_cause(void) { ++cleared; return 0; }
int wdt_install_timeout(const struct device *dev, const struct wdt_timeout_cfg *cfg)
{
	assert(dev == &test_watchdog_device && cfg->flags == WDT_FLAG_RESET_SOC);
	assert(cfg->window.min == 0 && cfg->window.max == 5000);
	++installations; return 0;
}
int wdt_setup(const struct device *dev, uint8_t options)
{
	assert(dev == &test_watchdog_device && options == 0); ++starts; return 0;
}
int wdt_feed(const struct device *dev, int channel)
{
	assert(dev == &test_watchdog_device && channel == 0); atomic_fetch_add(&feeds, 1); return 0;
}
static void *late_progress(void *arg)
{
	(void)arg;
	supervisor_enter(PHASE_SLEEP, 86405000);
	atomic_store(&returned, 1);
	return NULL;
}

int main(int argc, char **argv)
{
	assert(argc == 2);
	uint32_t cause;
	if (strcmp(argv[1], "missing-watchdog") == 0) {
		ready = false;
		assert(supervisor_init(&cause) == -ENODEV);
		assert(!installations && !starts && !atomic_load(&feeds));
		puts("PASS missing watchdog fails initialization without feeding");
		return 0;
	}
	assert(supervisor_init(&cause) == 0);
	assert(cause == 0x1234 && cleared == 1 && installations == 1 && starts == 1);
	supervisor_enter(PHASE_DNS, 3000);
	k_sleep(K_MSEC(600));
	assert(atomic_load(&feeds) >= 1);
	if (strcmp(argv[1], "modem-fault") == 0) {
		nrf_modem_fault_handler(NULL);
	} else {
		assert(strcmp(argv[1], "expired-main") == 0);
		supervisor_enter(PHASE_DNS, 50);
	}
	k_sleep(K_MSEC(800));
	int stopped_at = atomic_load(&feeds);
	k_sleep(K_MSEC(600));
	assert(atomic_load(&feeds) == stopped_at);
	pthread_t late;
	assert(pthread_create(&late, NULL, late_progress, NULL) == 0);
	assert(pthread_detach(late) == 0);
	k_sleep(K_MSEC(100));
	assert(!atomic_load(&returned) && atomic_load(&feeds) == stopped_at);
	puts("PASS production supervisor stops feeding after fault/expiry; late main cannot resume");
	return 0;
}
