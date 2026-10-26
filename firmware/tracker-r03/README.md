# Tracker r03: signed boot and a bounded firmware trial

Prototype only. The target builds and the actual image signatures verify against
the public key embedded in the built bootloader. No collar has been flashed.
Production signing-key custody, provisioning, update delivery and powered-device
acceptance remain open. The unchanged PCB is still the r05l design.

This revision keeps r02's GNSS/LTE-M, persistent outbox, HTTPS, bounded DNS and
watchdog recovery. It adds MCUboot with P-256 signatures, validation of the primary
image on every boot, bootloader flash protection and version-based downgrade
prevention. A lower application version is rejected; equal versions are allowed
by the pinned bootloader. This is not a hardware monotonic counter or debug-lock
policy. An attacker with physical debug/erase access is outside that protection.

A trial image remains unconfirmed until it has persisted a fresh valid GNSS fix,
received an upload acknowledgement and run at least 30 seconds. An independent
monitor requires confirmation within 600 seconds. Failure requests the existing
watchdog reset so MCUboot can revert an unconfirmed trial. No coverage, no usable
GNSS fix or failed storage/confirmation means the trial must revert. A normal
factory image with an unset trailer is already considered confirmed by MCUboot;
its default empty endpoint can therefore collect offline records.

## Build and inspect

Use the [pinned SDK and Python dependencies](../tracker/README.md). Supply an
owner-only ECDSA P-256 private key from outside the SDK. The build helper rejects
the SDK's public test key even when copied or renamed. This checkpoint uses a
locally generated **development-only** key. Its public half is retained in the
evidence; the private half is ignored and is never committed. Do not treat it as
an approved production key or automatically lock a device to it.

```sh
python3 scripts/build_tracker_r03.py \
  --sdk-root /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1 \
  --build-dir /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-tracker-r03-NEW \
  --signing-key /absolute/path/to/an/owner-only/development-key.pem
python3 scripts/test_tracker_r03.py
python3 scripts/verify_tracker_r03.py
```

Use an empty build directory. Sysbuild explicitly forwards `USER_CACHE_DIR` to
both child CMake processes; the application also forwards it to TF-M's nested
CMake command. The parent or namespaced setting alone does not do that in this
SDK. Check all four cache announcements; caches belong inside the workspace roots.

The new `collar_update_r05l/nrf9151/ns` target builds MCUboot and TF-M/application
together. See the [memory map](../boards/goksel/collar_update_r05l/UPSTREAM.md).
The inspection helper verifies both separately signed HEX/BIN files, their common
payload, the embedded verification key, all three reset vectors, compiled settings
and storage exclusion. It then merges only the two disjoint code images into
`collar-tracker-r03-prototype.hex`. ECDSA signatures may differ between independent
signing invocations; the signed content must match.

The SDK's image header carries `IMAGE_F_ROM_FIXED` and `load_addr=0x50000`.
The pinned swap-mode MCUboot boots at primary + header (`0x10200`) and does not
use that field as its entry point. Direct-XIP, RAM-load and header-load-address
checking are disabled and checked in the compiled configuration. The TF-M reset
vector and its non-secure application address are independently inspected.

## Update and migration limits

There is **no update downloader or staging command yet**. `IMG_MANAGER` support
does not provide a remote update service. With swap-offset, an update must begin
one erase sector into the secondary slot, at `0x81000`; writing its header at
`0x80000` is wrong. The pinned NCS `dfu_target_mcuboot.c` initializes its stream at
the slot base, so do not connect FOTA download to this mode without resolving
that mismatch. Zephyr's `flash_img` API has offset handling that needs an actual
staging integration and fault tests before use.

r01/r02 have no MCUboot and use a different primary layout. Installing r03 needs
a separately reviewed factory/SWD migration, including preservation of the NVS
sequence reservation and record CRC state. A full-chip erase can reuse sequence
numbers under the same identity; do not pair that with the existing server
identity without an explicit migration policy. The generated HEX excludes NVS
and TF-M storage, but a programmer's erase mode can still destroy them.

## Evidence and limits

[Saved build/test evidence](../evidence/tracker-r03/build-evidence.json) records
the exact source and artifact identities. The application trial tests execute
the actual guard with a POSIX kernel adapter, an accelerated clock and mocked
boot APIs under ASAN/UBSAN. Reset exit 42 is a host sentinel, not an observed SoC
reset. Nine image/key negative controls are retained separately.

The MCUboot host simulator uses the pinned bootutil sources and upstream flash
geometries. Its TinyCrypt crypto backend differs from the target's Nordic Oberon.
It does not execute the actual ARM image or the collar flash driver. See its
saved result for the exercised configuration and any unavailable checks.

Hardware trial/revert, watchdog handoff through a long swap, power loss during
swap/confirmation, flash protection, real GNSS/LTE-M/TLS, boot stack margins and
current draw remain untested. Production credentials, API deployment, approved
battery/assembly, factory/SMT, RF and ingress acceptance are also unfinished.
