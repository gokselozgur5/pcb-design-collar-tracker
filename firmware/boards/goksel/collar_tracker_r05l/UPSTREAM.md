# Memory-map provenance

`collar-memory.dtsi` adapts the Apache-2.0 nRF91 memory map from
[sdk-zephyr at 33fa6a7](https://github.com/nrfconnect/sdk-zephyr/blob/33fa6a7aac6a4401d16a67cb9f27a3483fa02dd6/dts/vendor/nordic/nrf91xx_partition.dtsi).
The upstream copyright notice and [license](LICENSE.Apache-2.0) are retained.

The SRAM and secure-storage regions are retained. The unused MCUboot region and
secondary image are removed: this prototype boots TF-M at zero and the
non-secure application at `0x40000`, with 256 KiB allocated to each. Addresses
`0x80000..0xeffff` are reserved. Application NVS stays at `0xf8000..0xfffff`.
This layout does not implement signed boot, OTA updates or rollback protection.
Do not enable MCUboot against this layout without a reviewed migration.
