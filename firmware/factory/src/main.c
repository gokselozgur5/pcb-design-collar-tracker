/* Factory observation firmware. Not the shipping tracker application. */
#include <errno.h>
#include <stdint.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/printk.h>
#include "board_contract.h"

#define IO DT_NODELABEL(board_io)
#define VIO_SETTLE_MS 1000
static const struct device *const bus = DEVICE_DT_GET(DT_NODELABEL(i2c2));
static const struct device *const accel = DEVICE_DT_GET(DT_NODELABEL(accelerometer));
static const struct gpio_dt_spec charge = GPIO_DT_SPEC_GET(IO, charge_status_gpios);
static const struct gpio_dt_spec fault = GPIO_DT_SPEC_GET(IO, charge_fault_gpios);
static const struct gpio_dt_spec alert = GPIO_DT_SPEC_GET(IO, fuel_alert_gpios);
static const struct gpio_dt_spec health_en = GPIO_DT_SPEC_GET(IO, health_enable_gpios);

static int read_gauge_word(uint8_t reg, uint16_t *value)
{
	uint8_t bytes[2];
	int rc = i2c_write_read(bus, DT_REG_ADDR(DT_NODELABEL(battery_gauge)),
			    &reg, 1, bytes, sizeof(bytes));
	if (rc == 0) {
		*value = sys_get_be16(bytes);
	}
	return rc;
}

static int init_gpio(void)
{
	const struct gpio_dt_spec *inputs[] = {&charge, &fault, &alert};
	for (size_t i = 0; i < ARRAY_SIZE(inputs); ++i) {
		if (!gpio_is_ready_dt(inputs[i])) { return -ENODEV; }
		int rc = gpio_pin_configure_dt(inputs[i], GPIO_INPUT);
		if (rc != 0) { return rc; }
	}
	/* Match the existing EN pulldown. No expansion module is selected:
	 * leave its SPI, RESET and interrupt pins disconnected. */
	if (!gpio_is_ready_dt(&health_en)) { return -ENODEV; }
	return gpio_pin_configure_dt(&health_en, GPIO_OUTPUT_INACTIVE);
}

int main(void)
{
	printk("{\"event\":\"boot\",\"board\":\"r05l\",\"scope\":\"factory_observation\","
	       "\"radio_enabled\":false,\"vio_wait_ms\":%d}\n", VIO_SETTLE_MS);
	/* No pinctrl, sensor initialization or external GPIO writes before this. */
	k_msleep(VIO_SETTLE_MS);
	int gpio_rc = init_gpio();
	int bus_rc = device_init(bus);
	int accel_rc = bus_rc == 0 ? device_init(accel) : bus_rc;
	printk("{\"event\":\"init\",\"gpio_rc\":%d,\"i2c_rc\":%d,\"accel_rc\":%d}\n",
	       gpio_rc, bus_rc, accel_rc);
	while (true) {
		uint16_t version = 0, voltage = 0, soc = 0;
		int gauge_rc = bus_rc;
		if (gauge_rc == 0) { gauge_rc = read_gauge_word(0x08, &version); }
		if (gauge_rc == 0 && (version & 0xfff0u) != 0x0010u) { gauge_rc = -ENODEV; }
		if (gauge_rc == 0) { gauge_rc = read_gauge_word(0x02, &voltage); }
		if (gauge_rc == 0) { gauge_rc = read_gauge_word(0x04, &soc); }
		/* 78.125 uV/LSB; wide multiplication also handles invalid high readings. */
		int32_t battery_mv = gauge_rc == 0 ? (int32_t)((uint64_t)voltage * 625u / 8000u) : -1;
		struct sensor_value axes[3] = {0};
		int sample_rc = accel_rc;
		if (sample_rc == 0) { sample_rc = sensor_sample_fetch(accel); }
		if (sample_rc == 0) { sample_rc = sensor_channel_get(accel, SENSOR_CHAN_ACCEL_XYZ, axes); }
		int charge_state = gpio_rc == 0 ? gpio_pin_get_dt(&charge) : gpio_rc;
		int fault_state = gpio_rc == 0 ? gpio_pin_get_dt(&fault) : gpio_rc;
		int alert_state = gpio_rc == 0 ? gpio_pin_get_dt(&alert) : gpio_rc;
		printk("{\"event\":\"sample\",\"uptime_ms\":%lld,\"gauge_rc\":%d,"
		       "\"gauge_version\":%u,\"battery_mv\":%d,\"soc_raw\":%d,"
		       "\"accel_rc\":%d,\"accel_micro_ms2\":[%lld,%lld,%lld],"
		       "\"charge_active\":%d,\"fault_active\":%d,\"fuel_alert_active\":%d}\n",
		       (long long)k_uptime_get(), gauge_rc, version, battery_mv,
		       gauge_rc == 0 ? (int)soc : -1, sample_rc,
		       (long long)sensor_value_to_micro(&axes[0]),
		       (long long)sensor_value_to_micro(&axes[1]),
		       (long long)sensor_value_to_micro(&axes[2]),
		       charge_state, fault_state, alert_state);
		k_sleep(K_SECONDS(1));
	}
	return 0;
}
