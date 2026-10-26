# Signed-image memory map

This new board uses the pinned SDK's
[`nrf91xx_partition.dtsi`](https://github.com/nrfconnect/sdk-zephyr/blob/33fa6a7aac6a4401d16a67cb9f27a3483fa02dd6/dts/vendor/nordic/nrf91xx_partition.dtsi)
directly. The SDK retains its Apache-2.0 attribution. The custom I/O definitions
come from the preserved `collar_tracker_r05l` board; no DK external pins are used.

| Region | Address | Size |
|---|---:|---:|
| MCUboot | `0x00000` | 64 KiB |
| Primary signed TF-M + application | `0x10000` | 448 KiB |
| Secondary image | `0x80000` | 448 KiB |
| TF-M PS / ITS / OTP | `0xf0000` / `0xf4000` / `0xf6000` | 16 / 8 / 8 KiB |
| Application NVS | `0xf8000` | 32 KiB |

The primary header is 512 bytes, the secure vector is `0x10200`, and the
non-secure vector is `0x50000`. Secure RAM is 88 KiB, modem shared RAM 40 KiB,
and non-secure RAM 128 KiB. The secure bootloader target defines no external
I/O buses. The application retains the external-rail delay and deferred I2C.

The old standalone board starts TF-M at zero and the application at `0x40000`.
It cannot accept this layout as an ordinary application update. Preserve that
board and its evidence; review an explicit factory/SWD migration separately.
