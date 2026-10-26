# Tracker r01 prototype

This application adds GNSS acquisition, persistent offline positions and an mTLS
uplink to the actual r05l nRF9151 board. It is separate from the frozen
[factory observation image](../README.md). No board has been flashed or tested.
Build and host-test evidence cannot establish radio behavior or battery runtime.

The current firmware is a prototype, not a manufacturing image. MCUboot,
signed updates, watchdog recovery, credential provisioning and factory integration
remain unfinished. Do not ship it as the complete tracker firmware.

Saved [r01 evidence](../evidence/tracker-r01/build-evidence.json): the final custom
board build passed. Application flash/RAM are 106,020/27,000 bytes; TF-M flash/RAM
are 64,816/45,388 bytes, with a separate 40 KiB modem shared-memory reservation.
Seven receiver tests, six injected mutation failures, all 40 single-byte record
corruptions and two linked-image negative controls passed. Host C tests use
AddressSanitizer and UndefinedBehaviorSanitizer. These are simulated I/O failures,
not physical flash power-cut results. The exact merged image SHA-256 is
`38f87835aba1709f31c14800926eb89054842885d4b69931a93f28fa7cddcce8`.

## Behavior

1. Wait 1 second before configuring external GPIO or the I2C bus. Keep the unused
   health expansion disabled. The hardware charging interlock remains independent.
2. Mount the 32 KiB NVS partition and validate its stored schema, sequence metadata
   and record CRCs. A detected corrupt or incompatible record stops tracking without
   application reformatting. NVS itself performs recovery/garbage collection; its
   actual flash behavior still needs power-cut testing.
3. Initialize the modem and acquire an unassisted GNSS fix, allowing up to 90 seconds.
   Only a fix flagged valid with finite, in-range coordinates and a valid UTC date
   becomes a record. Failure does not fabricate a position or timestamp.
4. Persist a record before trying LTE-M. With provisioned credentials and a configured
   host, allow 60 seconds for network registration; send at most eight queued records.
   TLS connect and HTTP exchange have separate 30-second limits. DNS remains governed
   by the modem, without an application deadline; this must be resolved before release.
5. Delete only the oldest record after HTTP 200 and the exact matching acknowledgment.
   On a connection/response failure, leave it for a later cycle. Put the modem offline
   and sleep until the next nominal 300-second interval, with at least 60 seconds
   between cycles. This simple prototype cycle is not a power-optimized PSM design.

The 64-record queue holds about 5h20m at one valid fix every five minutes. When full,
it rejects the newest fix and reports `OUTBOX FULL` over RTT; it does not silently
overwrite existing records. This overflow policy and capacity need product review.
Sequence blocks of 256 are reserved durably before use. Reboots burn unused numbers;
gaps are expected. Acknowledged record IDs are never deliberately reused. Do not erase
NVS and then reuse the same device identity; factory reset/reprovisioning must issue a
new identity or preserve the sequence epoch.

Battery voltage comes from non-mutating MAX17048 reads; zero means unavailable.
The application does not log coordinates, keys or certificate contents. The optional
accelerometer is not used yet. Health sensing, motion triggers, lost-dog mode and
remote configuration remain open.

## Build on the existing Mac

The frozen base SDK lock is extended by [toolchain-lock.json](toolchain-lock.json).
The exact Python environment is [python-requirements.lock](python-requirements.lock).
The SDK is NCS 3.4.1 and uses the pinned Zephyr GNU 1.0.1 compiler. TF-M's SDK
experimental notice remains visible; it was not suppressed. The optional `dtc`
executable is absent; the SDK's Python devicetree generator is used.

```sh
cd /Users/gok/codex/projects/collar-tracker
python3 scripts/test_tracker_firmware.py \
  --python /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/venv/bin/python
python3 scripts/build_tracker_firmware.py \
  --sdk-root /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1 \
  --build-dir /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-tracker-next
```

Use a new empty build directory for each changed configuration. NCS 3.4.1 generated
malformed quoted security options during one incremental reconfigure; a fresh build
avoids that stale cache and preserves diagnostics. The helper refuses to reuse a
nonempty directory. It never flashes hardware or edits the SDK revisions.

For a new SDK checkout, follow the base [setup](../README.md) and add the modules in
the tracker lock. The west project filter must include `mcuboot`, `mbedtls`,
`oberon-psa-crypto`, `trusted-firmware-m`, `tf-psa-crypto`, `qcbor`, `t_cose`, `zcbor`
and `cjson` in addition to the base modules. Pass `--` before a west config value
starting with `-`. Install the tracker Python lock in that SDK's own venv.

This board uses a [standalone memory map](../boards/goksel/collar_tracker_r05l/UPSTREAM.md):
TF-M resets at zero; the non-secure application starts at `0x40000`. Each gets
256 KiB. Secure storage starts at `0xf0000`; application NVS occupies
`0xf8000..0xfffff`. The merged HEX must contain both reset vectors and no storage
data. `scripts/inspect_tracker_image.py` checks the actual linked image and compiled
UART/security settings. Never flash the application-only HEX as a complete image.

## Configuration and receiver

Defaults deliberately contain no host, device ID or private credentials. They collect
offline fixes without attempting an upload. A private, ignored config file can set:

```ini
CONFIG_TRACKER_DEVICE_ID="collar-01"
CONFIG_TRACKER_HOST="your-real-api-host.example"
CONFIG_TRACKER_PORT=443
CONFIG_TRACKER_SEC_TAG=42
```

Pass that file with `--config /absolute/path/to/local.conf`. The example host above
is a placeholder, not a service. Host is a DNS name only; the endpoint is fixed at
`POST /v1/positions`. The modem must already contain a CA chain, unique client
certificate and private key at the selected tag. The client certificate's CN must
match the device ID. This app only checks for credentials and never writes or deletes
them. Production key generation, enrollment, revocation and debug lock are not yet
implemented. Use a tested nRF9151 modem firmware and an activated LTE-M nano-SIM;
neither is established by a successful application build.

The [local receiver](../receiver/README.md) validates client certificates and commits
idempotent records before replying. Tests send the actual C-generated JSON over a
local TLS connection, including a sequence above JavaScript's exact integer range.
This does not exercise the modem TLS stack or a cellular network.

## Next qualification

First complete provisioning, timeout/recovery and signed-update design. Then test
the actual board with J7/SWD and a current-limited source: VIO timing, gauge, reset
vectors, GNSS antenna/cold start, LTE-M attach, TLS and repeated power cuts across
NVS writes/deletes. Confirm pending records replay after an accepted request whose
response is lost. Measure power and decide reporting/overflow policies from real
data. Do not reuse the factory image's physical status or assume compile success
proves a working radio. Pack, harness, assembly and immersion acceptance remain
separate open gates in [STATUS](../../docs/STATUS.md).
