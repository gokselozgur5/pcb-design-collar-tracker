# Tracker r02 recovery prototype

r02 adds an application DNS deadline, a hardware-watchdog supervisor and modem
fault recovery to the frozen [r01 tracker](../tracker/README.md). It reuses the
same board, persistent outbox and [local receiver](../receiver/README.md). The PCB,
factory image, r01 evidence and assembly are unchanged. No hardware has been flashed.

This remains a prototype. Signed boot/updates, credential provisioning and factory
integration are unfinished. There is no supplied live endpoint, device identity,
credential set, approved battery or measured power budget. The default build only
collects offline positions. Build and host results do not qualify an assembled tracker.

## Failure behavior

| Condition | r02 action |
|---|---|
| DNS has not completed in 30 seconds | Return a timeout to main. The one resolver thread retains ownership of the call and any eventual result. |
| DNS finishes after the deadline | Free the SDK allocation and discard the answer. Do not start another resolver call while the previous worker owns the slot. |
| DNS remains stuck after modem offline | Wait up to 15 seconds for the worker, under one 20-second cleanup lease covering offline plus drain. Request watchdog reset if it does not finish. |
| A modem/flash/network phase stalls | The supervisor stops feeding when that phase's progress deadline expires. The watchdog is configured for a 5-second SoC reset. |
| Modem fault callback fires | Set an atomic fault flag in interrupt context. Stop feeding; do not invoke AT, flash, logging or modem reinitialization from the callback. |
| Main returns after its deadline | A failed lease stays failed. Returning late cannot resume watchdog feeds. |
| Boot follows watchdog or CPU lockup | Wait 120 seconds before modem initialization to limit repeated restart attempts. |
| Store mount/schema/CRC fails | Remain in a monitored service hold without starting the modem or deliberately formatting NVS. |
| Queue mutation or acknowledgment is uncertain | Keep the stored records and reset so boot reconciliation can recover them. |

The permanent resolver copies a fixed IPv4/IPv6 address before releasing SDK memory.
Main never aborts it or reads an SDK-owned pointer. This addresses the documented
[lack of a direct modem DNS timeout/cancel API](https://devzone.nordicsemi.com/f/nordic-q-a/128856/is-there-a-way-to-bound-timeout-nrf_getaddrinfo-dns-resolution-on-nrf91/569841).
Putting the modem offline is an attempt to drain the call, not a cancellation guarantee.
Only a completed worker or a full watchdog reset permits a fresh attempt.

The watchdog uses `wdt0` from the compiled non-secure board. Nordic's
[nRF9151 reset table](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/pmureset.html)
lists watchdog reset for both CPU and modem. Hardware reset behavior has not been
observed on this board. The supervisor checks every 500ms, keeps the watchdog active
in CPU sleep and debug halt, and never uses System OFF. Startup before watchdog
initialization is outside this protection. Power and reset timing need measurement.

Default phase leases are: boot/modem 30s; storage 10s; GNSS 100s (90s acquisition
plus 10s allowance); LTE attach 70s (60s plus 10s); DNS 32s; TLS connect and HTTP
35s each (existing 30s operations); socket close 5s; offline/drain 20s. Idle sleep
gets its finite requested duration plus 5s. Only main advances these leases.
The supervisor cannot make a deadlocked operation return; its fallback is reset.

The earlier 64-record queue, 300-second nominal cycle, oldest-first delivery and
reject-newest overflow policy are unchanged. A reset never deliberately erases NVS.
Actual power-cut behavior still requires physical testing. A 120-second cooldown
is not a qualified battery/runtime policy; watchdog wakes and repeated boot sequence
reservations also have an energy/flash cost. GNSS and IPv4/IPv6 operator behavior,
thread-stack margin, modem/TLS timing and restart recovery remain unmeasured.

## Verification and build

The [r02 evidence](../evidence/tracker-r02/build-evidence.json) records exact compiled
inputs and artifacts. The clean target build passed: application flash/RAM are
110,608/30,560 bytes; TF-M flash/RAM are 64,816/45,388 bytes, with a separate
40 KiB modem shared-memory reservation. The complete image SHA-256 is
`7d7b6d7bad55d9dc22b2e6c40b726065f6b02bc5dd1e17466a976b5d750c11a1`.
Portable policy tests exercise 30 ordered DNS deadline races,
sticky expiry, invalid phases and overflow guards. Host tests compile the actual DNS
and supervisor C files with a POSIX scheduling adapter and fake modem/watchdog I/O.
They check bounded caller return, no overlapping resolver, late-result freeing,
IPv4/IPv6 copies, fault/expiry feed stopping and missing-watchdog initialization.
AddressSanitizer and UndefinedBehaviorSanitizer are enabled. These tests do not
emulate Zephyr scheduling, real DNS, modem recovery or a physical watchdog reset.

The linked-image checks reject two valid-checksum HEX mutations (reset into storage
and an NVS overwrite) and two configuration mutations (watchdog disabled or secure
only). They preserve the r01 standalone TF-M map: reset at zero, application at
`0x40000`, application NVS at `0xf8000..0xfffff`. No programmed bytes enter storage.
The merged HEX is the complete prototype image; the application-only HEX is not.

```sh
cd /Users/gok/codex/projects/collar-tracker
python3 scripts/test_tracker_r02.py
python3 scripts/verify_tracker_r02.py
python3 scripts/build_tracker_r02.py \
  --sdk-root /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1 \
  --build-dir /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-tracker-r02-next
python3 scripts/inspect_tracker_r02.py \
  /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-tracker-r02-next
python3 scripts/test_tracker_r02_image.py \
  /Volumes/GOKSSD/codex/toolchains/collar-ncs-3.4.1/build-tracker-r02-next
```

Use a new empty build directory and the unchanged [SDK extension lock](../tracker/toolchain-lock.json)
and [Python lock](../tracker/python-requirements.lock). The build helper never flashes.
Private `--config` overrides work as in r01; do not publish private credentials or
claim the default empty host is a working service. `CONFIG_TRACKER_DNS_SECONDS`
defaults to 30, with an allowed range of 5..120. Host timing tests shorten it to 1s.

## Next

Implement provisioning and signed-update/migration support in a separate revision,
preserving these source/evidence identities. Then test an actual board and activated
Türkiye LTE-M SIM: GNSS, upload, lost replies, power cuts, stuck DNS/AT calls,
modem faults, watchdog reset/cooldown and measured current. The hardware interlock,
pack, assembly, RF and immersion gates in [STATUS](../../docs/STATUS.md) remain open.
