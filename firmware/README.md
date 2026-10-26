# Collar firmware — factory observation candidate

The r05l board now has a custom Zephyr target and a compiled factory observation
image. It reads the LIS2DW12 accelerometer, MAX17048 voltage/SOC registers and
the charger's status/fault pins. It reports JSON lines over SEGGER RTT through
the J7 SWD fixture. There is no connected UART on this PCB.

**Build verified; no board has been flashed or tested.** This is a secure,
standalone diagnostic image, not the shipping tracker application. LTE, GNSS,
upload/storage, update/recovery, provisioning and production acceptance remain
unfinished. The modem is not initialized and no radio transmission is requested.

## Hardware behavior

- The TWIM controller and accelerometer use deferred initialization. `main()`
  waits 1000ms before external GPIO configuration or I2C traffic, preserving the
  existing VIO startup allowance. Driver pinctrl does not run before that wait.
- SDA/SCL are P0.00/P0.01. The LIS2DW12 is at 0x19 because CS and SA0 are tied
  to VIO. The MAX17048 is at 0x36. The build checks seven native signal mappings
  against the current schematic and checks 14 compiled board conditions.
- CHG_STAT, CHG_FAULT and FG_ALERT are inputs with the board's existing pullups.
  Reported values are instantaneous active-low levels, not decoded charger
  phases or fault causes. Negative values indicate GPIO errors.
- HEALTH_EN follows its existing pulldown. The unselected extension port's SPI,
  RESET and interrupt pins remain disconnected. Heart-rate sensing is absent.
- Gauge reads do not reset, quick-start, calibrate or alter the battery gauge.
  SOC is reported as its raw 1/256-percent register and is not a runtime estimate.
  Failed reads have explicit error codes; voltage/SOC are -1 on failure.
- The charge-temperature interlock remains independent hardware. A successful
  sensor read would not qualify the pack, interlock or complete device.

The initial image uses **46,872 bytes of flash and 8,256 bytes of RAM**.
The intentional wrong-pin/early-I2C overlay fails compilation on both conditions.
[Saved build evidence](evidence/factory-r01/build-evidence.json) and
[negative compile control](evidence/factory-r01/negative-control.json) record the
result. A local ELF/HEX was generated; binary bytes remain in the local build
directory. Saved evidence verification checks source identity and recorded build
results; it does not rerun the compiler or a physical test.

## Build on the existing Mac

The portable SDK is under the mounted SSD, with no `/opt/nordic` installation or
global CMake registry changes. [toolchain-lock.json](toolchain-lock.json) pins the
nRF Connect SDK 3.4.1 repositories, Zephyr SDK 1.0.1 archives and their SHA256s.
Python dependencies are pinned in [requirements-build.txt](requirements-build.txt).

```sh
cd /Users/gok/codex/projects/collar-tracker
python3 scripts/build_factory_firmware.py \
  --sdk-root /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1 \
  --build-dir /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-factory-final
python3 scripts/verify_factory_firmware.py
```

Local HEX: `/Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-factory-final/zephyr/zephyr.hex`.
The fixture must reference J7.1 to the board's 1.8V VIO and use the actual
SWDIO/SWDCLK/GND mapping. Flashing and powered tests have not been performed.

The negative control uses a separate, new build directory:

```sh
python3 scripts/test_factory_firmware.py \
  --sdk-root /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1 \
  --build-dir /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-factory-invalid-02 \
  --log .runtime/factory-invalid-02.log
```

For a new SDK workspace, clone `nrfconnect/sdk-nrf` at `v3.4.1`, create a local
Python 3.12 venv, install the pinned Python requirements, and run `west init -l nrf`.
Set `manifest.project-filter` to
`-.*,+zephyr,+cmsis,+cmsis_6,+hal_nordic,+nrfxlib,+segger,+hal_st,+bsim` before
`west update --narrow -o=--depth=1`. Confirm the resulting commits against the lock.
For this Apple Silicon host, extract the hash-verified minimal SDK archive into
the workspace and the ARM archive into its `zephyr-sdk-1.0.1/gnu/` directory.
The build helper sets explicit compiler/cache/temp paths and uses `--no-sysbuild`.
Other platforms need their corresponding official SDK archive and a fresh build.

The build emits Zephyr's intentional assertions-enabled CMake notice. The optional
native `dtc` executable was absent; Zephyr's Python devicetree generation and C
assertions ran successfully. No compiler warning suppression was added.
