#include "supervisor.h"
#include <errno.h>
#include <modem/nrf_modem_lib.h>
#include <zephyr/device.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/watchdog.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/printk.h>

static const struct device *const watchdog = DEVICE_DT_GET(DT_NODELABEL(wdt0));
static struct progress_lease lease;
static struct k_spinlock lease_lock;
static int channel;
static atomic_t modem_failed;
K_SEM_DEFINE(supervisor_started, 0, 1);

/* Nordic invokes this in interrupt context. Do not call AT, flash, or logging. */
void nrf_modem_fault_handler(struct nrf_modem_fault_info *info)
{
	ARG_UNUSED(info);
	atomic_set(&modem_failed, 1);
}

static void monitor(void *a, void *b, void *c)
{
	ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
	k_sem_take(&supervisor_started, K_FOREVER);
	for (;;) {
		k_spinlock_key_t key = k_spin_lock(&lease_lock);
		if (atomic_get(&modem_failed)) { lease_fail(&lease); }
		bool feed = lease_feed_allowed(&lease, k_uptime_get());
		enum tracker_phase phase = lease.phase;
		k_spin_unlock(&lease_lock, key);
		if (!feed) {
			printk("Recovery: watchdog feed stopped in phase %d\n", phase);
			return; /* Hardware resets CPU and modem, including a stalled scheduler. */
		}
		if (wdt_feed(watchdog, channel)) {
			key = k_spin_lock(&lease_lock);
			lease_fail(&lease);
			k_spin_unlock(&lease_lock, key);
			return;
		}
		k_sleep(K_MSEC(500));
	}
}
K_THREAD_DEFINE(supervisor_thread, 1024, monitor, NULL, NULL, NULL, 0, 0, 0);

int supervisor_init(uint32_t *cause)
{
	*cause = 0;
	int ret = hwinfo_get_reset_cause(cause);
	if (ret) { return ret; }
	ret = hwinfo_clear_reset_cause();
	if (ret) { return ret; }
	if (!device_is_ready(watchdog)) { return -ENODEV; }
	struct wdt_timeout_cfg cfg = {.flags = WDT_FLAG_RESET_SOC, .window = {.min = 0, .max = 5000}};
	channel = wdt_install_timeout(watchdog, &cfg);
	if (channel < 0) { return channel; }
	/* Keep running during CPU sleep and debugger halt. Never enable System OFF. */
	ret = wdt_setup(watchdog, 0);
	if (ret) { return ret; }
	if (!lease_init(&lease, k_uptime_get(), 30000)) { return -EINVAL; }
	k_sem_give(&supervisor_started);
	return 0;
}

void supervisor_enter(enum tracker_phase phase, uint32_t budget_ms)
{
	k_spinlock_key_t key = k_spin_lock(&lease_lock);
	if (atomic_get(&modem_failed)) { lease_fail(&lease); }
	bool okay = lease_enter(&lease, k_uptime_get(), phase, budget_ms);
	k_spin_unlock(&lease_lock, key);
	if (!okay) { supervisor_reset("Expired or failed progress lease"); }
}

FUNC_NORETURN void supervisor_reset(const char *reason)
{
	k_spinlock_key_t key = k_spin_lock(&lease_lock);
	lease_fail(&lease);
	k_spin_unlock(&lease_lock, key);
	printk("Recovery requested: %s\n", reason);
	for (;;) { k_sleep(K_FOREVER); }
}

FUNC_NORETURN void supervisor_service_hold(const char *reason)
{
	printk("SERVICE HOLD: %s; storage is preserved\n", reason);
	/* Main is still executing and radio has not started or has gone offline.
	 * A known permanent fault must not create an endless flash/reset loop. */
	for (;;) {
		supervisor_enter(PHASE_SERVICE, 15000);
		k_sleep(K_SECONDS(5));
	}
}

void supervisor_sleep(uint32_t duration_ms)
{
	/* A single finite deadline bounds even a stuck idle loop. */
	supervisor_enter(PHASE_SLEEP, duration_ms + 5000);
	k_sleep(K_MSEC(duration_ms));
}
