# Current state — 2026-10-25

**Active: Paul layout fixes, physical nano-SIM and two real JLC DFM passes.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All repository and GitHub content is English. The new board is unfinished.

| Item | Verified state | Evidence |
|---|---|---|
| Accepted PCB DFM baseline | 0.3.4, 35 × 28 mm; two JLC runs at 0 Danger / 0 Warning | `evidence/release-034/` |
| Current implementation | `experiments/paul-nanosim-r04f-40x32/hardware/`, 40 × 32 mm | Native board and `growth-trial.json` |
| Current native routing | Zero opens, violations, warnings or parity issues | Trial `evidence/partial-returns-drc.json` |
| Ground | 81 pads, 81 GND vias; both inner layers are continuous GND fills, no inner tracks | Trial `evidence/layout-inventory.json` |
| RF | 24 baseline segments retained exactly | Same inventory; physical RF performance remains unqualified |
| Return-via screen | 9 of 83 non-GND vias outside the inherited 2 mm screen | Same inventory; still to resolve |
| New revision JLC | Not run | Old acceptance does not transfer |
| Production readiness | Power, RF, BOM, SMT, firmware, fixture and mechanics remain open | `docs/pcba-delivery.md` |

## Continue from r04f

The user authorized growth if measured routing required it. The 40 × 32 mm trial
keeps the component placement, pads and rules; it expands the outline and both
inner GND boundaries. Routing reduced five opens to one; moving one local ground exit and completing
the final SIM supply route closed the last connection. Fifteen return vias were
added and both unused charger vias removed. This is a separate
experiment, not acceptance of a larger enclosure.

Current PCB SHA256:
`240be3bbab528ffb123737fe75c54bb642ec2f204b32a6533e704f794691a6d2`.
`evidence/routing-checkpoint.json` binds the current source and checks.
`build/connected-before-returns.kicad_pcb` preserves the first native-clean stage. Native DRC must run beside
the matching project and schematic. Check live hashes/processes before resuming.

**Next: resolve nine remaining return-via screen gaps.** The 15 added vias reduce
30 gaps to nine, with all new via centers in both inner GND fills and native DRC
still clean. The report remains explicitly partial; do not erase failed IDs.
Four gaps cluster around the SIM/sensor area, others around signal transitions.
The current inventory has their exact positions and distances.

The final route became possible after moving the U1 central GND via from
(111,114.3) to (111.7,114.4), preserving its short local return. Actual copper
connectivity shows all 81 GND pads reach a GND via with the planes excluded.
Native routing is complete. Power/ESD/passive review and English labels remain.

The current copper-only power estimate keeps the main supply paths connected.
The auxiliary J5 branch is 39.50 mm with estimated 52.16 mΩ at 20 °C under the
report's assumptions. These are geometric estimates, not thermal, transient,
cell, ferrite, connector or bench acceptance. Review the actual power paths and
short necks before release; a netclass width alone proves nothing.

## Router defects resolved

Native copper contacts and router contacts differed. Exact-center connectors,
split junctions and 0.0001 mm coordinates reduced the old r04d model's 61 reported
incompletes to the same six native opens. The minimal connectors add no copper
outside the original shapes within the recorded 0.0002 mm comparison tolerance.
An isolated no-route SES round-trip preserved native connectivity and ground.

KiCad's `(type route)` was also loaded as `USER_FIXED` by Freerouting. The exporter
now uses `(type normal)` for intentionally movable signals, preserving `(type fix)`.
The loaded-state regression rejects the old model (930 USER_FIXED items) and
accepts the corrected model (275 merged UNFIXED polylines/vias; 241 fixed items
unchanged). See r04e `evidence/route-lock-regression.json` and RESUME.

## Preserved checkpoints

- `paul-nanosim-r04e`: 35 × 28 mm, five opens, eight dangling warnings, zero other
  native violations/parity. SHA256
  `1628a83a707b4b8e541ee8ce598531841419c5f31f4a7d4e4456ea6fc5c65ff8`.
  All 81 GND pads have an actual local copper path to a GND via, planes excluded.
- r04e `build/routed-unlocked-raw.kicad_pcb`: rejected alternative. It closed the
  original SIM lines but opened other pins and sent the J5 supply along 83.52 mm
  of copper, including 14.91 mm of narrow trace. It is not the active board.
- `paul-nanosim-r04d`: unchanged six-open checkpoint; source SHA256
  `38882bf0111a0190a9a55e756b72be96f91e325de29d909a93c6a57759bbed44`.
- r04 and rejected r04c remain preserved. The original SIM opening toward y=100
  is correct. Do not repeat the rejected 180-degree socket reversal.

Builders reproduce initial stages only. Never run them over an existing trial.
Later native snapshots and source-bound evidence preserve the actual rework.

## Remaining acceptance

1. Resolve the nine return-screen gaps while preserving native DRC and connectivity.
2. Review power, ESD topology, passive copper balance and short ground returns.
3. Add local return vias, refill both planes and verify actual connections.
4. Place useful English labels and inspect copper, mask, paste, drill and silk.
5. Pass native DRC/ERC/parity and two fresh unchanged-rule JLC runs of identical
   final ZIP bytes. Preserve raw measurements, UI, PDFs and source/output hashes.
6. Keep the handoff current, commit coherent changes and deliver absolute paths.

Nano-SIM now, eSIM later. J5 is a digital expansion port, not a heart-rate sensor.
Factory assembly/programming/test is required. No order, payment, supplier
message, powered test or production approval has occurred.
