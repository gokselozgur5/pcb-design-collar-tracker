/* Prototype tracker; no physical radio, power or ingress qualification yet. */
#include "board_contract.h"
#include "outbox.h"
#include "uplink.h"
#include "dns.h"
#include "supervisor.h"
#include <errno.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <modem/lte_lc.h>
#include <modem/nrf_modem_lib.h>
#include <nrf_modem_gnss.h>
#include <zephyr/device.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/kernel.h>
#include <zephyr/kvss/nvs.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/timeutil.h>

struct fix_data {
	double latitude, longitude;
	float accuracy;
	struct nrf_modem_gnss_datetime datetime;
};
K_SEM_DEFINE(gnss_updated, 0, 1);
K_SEM_DEFINE(registered, 0, 1);
static atomic_t accepting_fixes;
static struct nvs_fs storage;
static struct outbox queue;
static const struct device *const bus = DEVICE_DT_GET(DT_NODELABEL(i2c2));
static const struct gpio_dt_spec health = GPIO_DT_SPEC_GET(COLLAR_IO, health_enable_gpios);

static int nvs_get(void *ctx, uint16_t key, void *out, size_t n)
{
	return (int)nvs_read(ctx, key, out, n);
}
static int nvs_put(void *ctx, uint16_t key, const void *in, size_t n)
{
	return (int)nvs_write(ctx, key, in, n);
}
static int nvs_remove(void *ctx, uint16_t key) { return nvs_delete(ctx, key); }

static int storage_init(void)
{
	const struct flash_area *area;
	int ret = flash_area_open(PARTITION_ID(storage_partition), &area);
	if (ret) { return ret; }
	struct flash_pages_info page;
	ret = flash_get_page_info_by_offs(area->fa_dev, area->fa_off, &page);
	if (ret) { flash_area_close(area); return ret; }
	if (page.size == 0 || area->fa_size % page.size || area->fa_size / page.size < 3 ||
	    area->fa_size / page.size > UINT16_MAX) { flash_area_close(area); return -EINVAL; }
	storage.flash_device = area->fa_dev;
	storage.offset = area->fa_off;
	storage.sector_size = page.size;
	storage.sector_count = area->fa_size / page.size;
	flash_area_close(area);
	ret = nvs_mount(&storage);
	if (ret) { return ret; } /* Do not format a failing or incompatible store. */
	struct outbox_io io = { &storage, nvs_get, nvs_put, nvs_remove };
	return outbox_init(&queue, &io);
}

static void gnss_event(int event)
{
	if (event != NRF_MODEM_GNSS_EVT_PVT || !atomic_get(&accepting_fixes)) { return; }
	/* This callback runs in interrupt context. Main reads and validates PVT. */
	k_sem_give(&gnss_updated);
}

static void network_event(const struct lte_lc_evt *event)
{
	if (event->type == LTE_LC_EVT_NW_REG_STATUS &&
	    (event->nw_reg_status == LTE_LC_NW_REG_REGISTERED_HOME ||
	     event->nw_reg_status == LTE_LC_NW_REG_REGISTERED_ROAMING)) {
		k_sem_give(&registered);
	}
}

static uint16_t battery_mv(void)
{
	uint8_t reg = 0x08, bytes[2];
	if (!device_is_ready(bus) || i2c_write_read(bus, 0x36, &reg, 1, bytes, 2) ||
	    (sys_get_be16(bytes) & 0xfff0U) != 0x0010U) { return 0; }
	reg = 0x02;
	if (i2c_write_read(bus, 0x36, &reg, 1, bytes, 2)) { return 0; }
	uint32_t mv = (uint64_t)sys_get_be16(bytes) * 625U / 8000U;
	return mv >= 2000 && mv <= 5000 ? (uint16_t)mv : 0;
}

static int position_from_fix(const struct fix_data *f, struct position *p)
{
	const struct nrf_modem_gnss_datetime *d = &f->datetime;
	if (!isfinite(f->latitude) || !isfinite(f->longitude) || !isfinite(f->accuracy) ||
	    f->latitude < -90 || f->latitude > 90 || f->longitude < -180 ||
	    f->longitude > 180 || f->accuracy <= 0 || f->accuracy > 1000000 ||
	    d->year < 2020 || d->year > 2099 || d->month < 1 || d->month > 12 ||
	    d->hour > 23 || d->minute > 59 || d->seconds > 59 || d->ms > 999) { return -EINVAL; }
	static const uint8_t days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
	unsigned max_day = days[d->month - 1] + (d->month == 2 && d->year % 4 == 0);
	if (d->day < 1 || d->day > max_day) { return -EINVAL; }
	struct tm utc = {.tm_year = d->year - 1900, .tm_mon = d->month - 1,
		.tm_mday = d->day, .tm_hour = d->hour, .tm_min = d->minute, .tm_sec = d->seconds};
	double lat = f->latitude * 1e7, lon = f->longitude * 1e7;
	*p = (struct position){
		.utc_ms = (uint64_t)timeutil_timegm64(&utc) * 1000 + d->ms,
		.latitude_e7 = (int32_t)(lat + (lat < 0 ? -0.5 : 0.5)),
		.longitude_e7 = (int32_t)(lon + (lon < 0 ? -0.5 : 0.5)),
		.accuracy_cm = (uint32_t)ceil((double)f->accuracy * 100),
		.battery_mv = battery_mv(),
	};
	return position_valid(p) ? 0 : -EINVAL;
}

static int acquire(struct position *p)
{
	int ret = lte_lc_func_mode_set(LTE_LC_FUNC_MODE_ACTIVATE_GNSS);
	if (ret) { return ret; }
	/* Configuration requires GNSS to be enabled in functional mode, but stopped. */
	if ((ret = nrf_modem_gnss_use_case_set(NRF_MODEM_GNSS_USE_CASE_MULTIPLE_HOT_START)) ||
	    (ret = nrf_modem_gnss_fix_interval_set(0)) ||
	    (ret = nrf_modem_gnss_fix_retry_set(CONFIG_TRACKER_FIX_SECONDS))) {
		return ret; /* Caller forces modem offline after every acquisition attempt. */
	}
	k_sem_reset(&gnss_updated);
	atomic_set(&accepting_fixes, 1);
	ret = nrf_modem_gnss_start();
	int64_t end = k_uptime_get() + CONFIG_TRACKER_FIX_SECONDS * INT64_C(1000);
	if (ret == 0) {
		ret = -ETIMEDOUT;
		while (k_uptime_get() < end) {
			int64_t remaining = end - k_uptime_get();
			if (remaining <= 0 || k_sem_take(&gnss_updated, K_MSEC(remaining))) { break; }
			struct nrf_modem_gnss_pvt_data_frame pvt;
			if (nrf_modem_gnss_read(&pvt, sizeof(pvt), NRF_MODEM_GNSS_DATA_PVT) ||
			    !(pvt.flags & NRF_MODEM_GNSS_PVT_FLAG_FIX_VALID)) { continue; }
			struct fix_data f = {pvt.latitude, pvt.longitude, pvt.accuracy, pvt.datetime};
			if (position_from_fix(&f, p) == 0) { ret = 0; break; }
		}
	}
	atomic_clear(&accepting_fixes);
	int stop = nrf_modem_gnss_stop();
	int off = lte_lc_func_mode_set(LTE_LC_FUNC_MODE_DEACTIVATE_GNSS);
	if (stop || off) { printk("GNSS stop=%d deactivate=%d\n", stop, off); }
	return ret;
}

static int drain(void)
{
	struct position p;
	supervisor_enter(PHASE_STORAGE, 10000);
	int ret = outbox_peek(&queue, &p);
	if (ret == -ENOENT) { return 0; }
	if (ret) { return ret; }
	k_sem_reset(&registered);
	supervisor_enter(PHASE_ATTACH, CONFIG_TRACKER_ATTACH_SECONDS * 1000U + 10000U);
	ret = lte_lc_connect_async(network_event);
	if (!ret) { ret = k_sem_take(&registered, K_SECONDS(CONFIG_TRACKER_ATTACH_SECONDS)); }
	if (ret) { return ret; }
	for (unsigned i = 0; i < 8; ++i) {
		supervisor_enter(PHASE_STORAGE, 10000);
		ret = outbox_peek(&queue, &p);
		if (ret == -ENOENT) { return 0; }
		if (ret) { return ret; }
		ret = uplink_send(&p);
		if (ret) { return ret; }
		supervisor_enter(PHASE_STORAGE, 10000);
		ret = outbox_ack(&queue, p.sequence);
		if (ret) { return ret; }
		printk("Position acknowledged: %llu\n", (unsigned long long)p.sequence);
	}
	return 0;
}

static void offline_and_drain_dns(void)
{
	/* AT shutdown and the non-cancellable resolver share one finite recovery
	 * lease. Never reinitialize the modem or reuse its job while DNS is alive. */
	supervisor_enter(PHASE_CLEANUP, 20000);
	int ret = lte_lc_func_mode_set(LTE_LC_FUNC_MODE_OFFLINE);
	if (ret) { supervisor_reset("Modem offline failed"); }
	if (!tracker_dns_wait_idle(15000)) { supervisor_reset("DNS worker did not finish"); }
}

int main(void)
{
	uint32_t reset_cause;
	int ret = supervisor_init(&reset_cause);
	if (ret) { printk("SERVICE HOLD: watchdog/reset-cause initialization %d; radio stays off\n", ret); return 0; }
	printk("Collar tracker r02 prototype; reset cause=%u; waiting 1000ms for VIO\n", reset_cause);
	k_msleep(1000);
	ret = gpio_is_ready_dt(&health) ? gpio_pin_configure_dt(&health, GPIO_OUTPUT_INACTIVE) : -ENODEV;
	if (ret) { supervisor_service_hold("Expansion disable failed"); }
	ret = device_init(bus);
	if (ret) { printk("Gauge unavailable: I2C init %d\n", ret); }
	supervisor_enter(PHASE_STORAGE, 10000);
	ret = storage_init();
	if (ret) { supervisor_service_hold("Persistent store mount or validation failed"); }
	if (reset_cause & (RESET_WATCHDOG | RESET_CPU_LOCKUP)) {
		printk("Recovery cooldown: 120 seconds before enabling the modem\n");
		supervisor_sleep(120000);
	}
	supervisor_enter(PHASE_MODEM, 30000);
	ret = nrf_modem_lib_init();
	if (ret) { supervisor_reset("Modem initialization failed"); }
	ret = lte_lc_func_mode_set(LTE_LC_FUNC_MODE_OFFLINE);
	if (ret) { supervisor_reset("Initial modem offline failed"); }
	ret = lte_lc_system_mode_set(LTE_LC_SYSTEM_MODE_LTEM_GPS, LTE_LC_SYSTEM_MODE_PREFER_AUTO);
	if (ret) { supervisor_reset("LTE-M/GNSS mode configuration failed"); }
	ret = nrf_modem_gnss_event_handler_set(gnss_event);
	if (ret) {
		supervisor_reset("GNSS handler setup failed");
	}
	int provisioned = uplink_configured();
	printk("Uplink provisioning result: %d (zero means configured)\n", provisioned);
	while (queue.healthy) {
		int64_t started = k_uptime_get();
		struct position p;
		supervisor_enter(PHASE_FIX, CONFIG_TRACKER_FIX_SECONDS * 1000U + 10000U);
		ret = acquire(&p);
		if (ret == 0) {
			supervisor_enter(PHASE_STORAGE, 10000);
			ret = outbox_enqueue(&queue, &p);
			printk("Position persistence: %d\n", ret);
			if (ret == -ENOSPC) { printk("OUTBOX FULL: newest fix rejected; older fixes retained\n"); }
		} else { printk("No usable GNSS fix: %d\n", ret); }
		offline_and_drain_dns();
		if (!queue.healthy) { supervisor_reset("Outbox mutation needs reboot reconciliation"); }
		if (queue.healthy && provisioned == 0) { printk("Uplink result: %d\n", drain()); }
		offline_and_drain_dns();
		if (!queue.healthy) { supervisor_reset("Outbox acknowledgment needs reboot reconciliation"); }
		int64_t wait = CONFIG_TRACKER_INTERVAL_SECONDS * INT64_C(1000) - (k_uptime_get() - started);
		/* Slow cycles never spin or immediately restart a failed connection. */
		supervisor_sleep((uint32_t)(wait > 60000 ? wait : 60000));
	}
	supervisor_service_hold("Tracker stopped");
}
