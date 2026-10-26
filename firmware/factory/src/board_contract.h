#ifndef COLLAR_BOARD_CONTRACT_H
#define COLLAR_BOARD_CONTRACT_H

#include <zephyr/devicetree.h>
#include <zephyr/dt-bindings/gpio/gpio.h>
#include <zephyr/dt-bindings/pinctrl/nrf-pinctrl.h>
#include <zephyr/sys/util.h>

/* Pin numbers are checked against the native r05l schematic before each build. */
#define COLLAR_IO DT_NODELABEL(board_io)
BUILD_ASSERT(DT_GPIO_PIN(COLLAR_IO, charge_status_gpios) == 10, "CHG_STAT pin mismatch");
BUILD_ASSERT(DT_GPIO_PIN(COLLAR_IO, charge_fault_gpios) == 11, "CHG_FAULT pin mismatch");
BUILD_ASSERT(DT_GPIO_PIN(COLLAR_IO, fuel_alert_gpios) == 13, "FG_ALERT pin mismatch");
BUILD_ASSERT(DT_GPIO_PIN(COLLAR_IO, health_enable_gpios) == 9, "HEALTH_EN pin mismatch");
BUILD_ASSERT(DT_GPIO_FLAGS(COLLAR_IO, charge_status_gpios) == GPIO_ACTIVE_LOW,
	     "CHG_STAT polarity mismatch");
BUILD_ASSERT(DT_GPIO_FLAGS(COLLAR_IO, charge_fault_gpios) == GPIO_ACTIVE_LOW,
	     "CHG_FAULT polarity mismatch");
BUILD_ASSERT(DT_GPIO_FLAGS(COLLAR_IO, fuel_alert_gpios) == GPIO_ACTIVE_LOW,
	     "FG_ALERT polarity mismatch");
BUILD_ASSERT(DT_GPIO_FLAGS(COLLAR_IO, health_enable_gpios) == GPIO_ACTIVE_HIGH,
	     "HEALTH_EN polarity mismatch");
BUILD_ASSERT(DT_REG_ADDR(DT_NODELABEL(accelerometer)) == 0x19, "LIS2DW12 SA0 mismatch");
BUILD_ASSERT(DT_REG_ADDR(DT_NODELABEL(battery_gauge)) == 0x36, "MAX17048 address mismatch");
BUILD_ASSERT(DT_PROP(DT_NODELABEL(i2c2), zephyr_deferred_init), "I2C must wait for VIO");
BUILD_ASSERT(DT_PROP(DT_NODELABEL(accelerometer), zephyr_deferred_init),
	     "Accelerometer must wait for VIO");
BUILD_ASSERT(DT_PROP_BY_IDX(DT_CHILD(DT_NODELABEL(board_i2c_default), group1), psels, 0)
	     == NRF_PSEL(TWIM_SDA, 0, 0), "I2C SDA pin mismatch");
BUILD_ASSERT(DT_PROP_BY_IDX(DT_CHILD(DT_NODELABEL(board_i2c_default), group1), psels, 1)
	     == NRF_PSEL(TWIM_SCL, 0, 1), "I2C SCL pin mismatch");

#endif
