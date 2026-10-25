# Current state — 2026-10-25

**r04i PCB: native-clean and two actual JLC runs at 0 Danger / 0 Warning.**
**Active r05f: five open connections, zero other native violations/warnings and 44 return-screen gaps.**
**Electrical release: HOLD; the proposed repair still needs source/bench qualification.**
**Swimming enclosure: engineering prototype under review; IP68 is not qualified.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All authored repository/GitHub content is English. Original supplier reports retain
their original metadata.

Review: [updated two-page PDF](../mechanical/swim-r02-fit/review.pdf) and
[132-file bundle](../release/collar-tracker-r04i-swim-r02-fit-review.zip).
Bundle SHA256: `ea960e01f39e7b31aef930359a82b7b360e9e6c4a1fb232dad78c8d7f7032206`.
`python3 scripts/verify_handoff.py` verifies the saved PCB, mechanical checks and
every bundled file against the checkout; it performs no new supplier/physical test.

## Active r05f circuit and layout

Continue from `experiments/power-r05f-return-reset/hardware/`, following its
[review and limits](../experiments/power-r05f-return-reset/README.md).
PCB SHA256: `1b2b4bd7b90c3931bd8cbb151637408902332a94260d4a2a820ae6df04838a09`.
The saved native source is authoritative; do not rerun a seed over it.

The unchanged 71-part r05 circuit adds rail supervision/restart hysteresis, GPIO
sequencing and a battery gauge. Its schematic identity and clear ERC are retained.
The seven existing circuit regressions and conditional calculations do not establish
powered behavior. Source retention, effective capacitor bounds and exact resistor
MPNs/tolerance/TCR still require qualification; electrical release remains on HOLD.
Nordic's conditional power-off exception is recorded in the
[sequencing follow-up](power-sequence-followup.md); review actual GPIO shutdown
behavior before treating source retention as an unconditional requirement.

| Current r05f check | Result |
|---|---|
| Outline / layers | 40 × 32 × 0.8 mm; four copper layers |
| Native DRC / parity | **Five non-GND opens; zero other violations, warnings or mismatches** |
| Open nets | NRF_ENABLE, VBAT, FG_ALERT; two VIO_ENABLE connections |
| Ground | 97 physical pads, 94 unique terminals with local paths; 83 GND vias |
| Planes / RF | Both continuous inner GND fills contain every GND via; no inner tracks; 24 original RF segments retained |
| Returns | **44 of 129 non-GND vias exceed the inherited 2 mm screen**; return placement is unfinished |
| SIM | Four clamp paths without bypass; 20 other bottom-side bodies clear the card entry strip |
| Power | All 12 original backbone checks pass; the new VDD_NRF control branch is connected |
| Supplier / mechanical | No r05f Gerber/JLC run; fresh preliminary fit checks 69 populated envelopes and 30 shell checks |

The sequence is preserved and verified: r05b had 14 opens, r05c eight, and r05f
five. r05d's strict joint Freerouting pass stayed at eight and no SES was imported.
r05e's native joint reroute ended with 17 opens and is not selected. r05f starts
from r05c, retaining the working original signals.

C9 moved closer to modem ENABLE and its local GND path shortened to 1.118 mm.
POWER_GOOD closed with a 68.085 mm candidate route; that detour still needs review.
Five unused signal exits, 14 unused single-layer via junctions, ten loose segments
and a 0.65 mm unused end were removed or replaced while preserving native terminal
groups. The extra space then allowed a 16.103 mm VDD_NRF control branch to connect.
No original power trunk was narrowed. Four raster regressions pass; source-bound
native checks cover the actual applied changes.

Twenty-five return-only GND stitches were released for rerouting. Their replacement
is still required: zero native geometry warnings does not mean an accepted return
layout. Local grounds, RF-adjacent grounds, native/supplier rules and manufacturer
lands were preserved. Exact-polygon and bounding-box planning models both separate
the remaining nets; those models are not proof that every native route is impossible.

**Next:** inspect the barriers at U7's enable pins, U4's enable exit and the gauge
connections. Make a small measured placement or crossing change in an isolated
copy, retaining working power, RF, SIM, local GND and both inner planes. Do not
repeat the unchanged search or remove all working trunks again. Complete the five
connections, restore and review returns, inspect passive attachments and update
the inherited `CT 0.5B` legend. Refresh populated fit, then export and obtain two
fresh same-ZIP JLC analyses. Source/BOM/pack/antenna/assembly/physical qualification
remain required before production.

## Preserved tested PCB

Source: `experiments/paul-nanosim-r04i-sim-access-40x32/hardware/`.
PCB SHA256: `f4be0288708733aaa6092a703ffa1bfebb3dc059fd21112a8cfed94028acc3b0`.
Final ZIP: `experiments/paul-nanosim-r04i-sim-access-40x32/evidence/collar-tracker-04i-final-40x32-dfm.zip`.
ZIP SHA256: `6304b66623a473e4c5405c6db7181b3f1879fa93088f9812802d43e814f90898`.

| Check | Result |
|---|---|
| Outline / layers | 40 × 32 mm; four copper layers; 55 footprints |
| Native DRC/ERC/parity | Zero violations, warnings, opens or schematic mismatches |
| Ground | All 82 GND pads have local track paths to vias; 91 GND vias join both continuous inner planes |
| Return screen | All 93 non-GND vias within the inherited 2 mm screen; no inner-layer tracks |
| RF identity | All 24 baseline RF segments retained; impedance/body performance still unqualified |
| SIM access | All 19 other bottom-side bodies/lands clear the projected card lane, including 0.20 mm lateral margin |
| SIM topology | All four connector paths pass through their clamp land; no same-net copper bypass |
| JLC PCB DFM | Records `637245503244296194` and `637247002053398530`; 29 analyzed rows and 442 green measurements each |
| JLC rules | Unchanged SHA256 `f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`; SMT off |

D1/C10 moved beside the card lane; D1 CLK/RST channels were exchanged in both
schematic and PCB. R12 moved to open a short protected reset crossing. The unused
old clock branch was removed. R12's two copper attachments are both 0.2 mm.
The first supplier run found 5 Danger / 2 Warning at the SIM legend; moving that
legend 1.476 mm resolved them. The failed package/report is preserved separately.
A later browser attempt never uploaded a file and is not counted as an analysis.
The helper now detects that condition instead of returning apparent success.

All final evidence is indexed in the trial's `evidence/routing-checkpoint.json`.
Preserve the tested bytes. Any later PCB change needs a new package and fresh checks.

## Electrical and connectivity review

The [power review](../evidence/power-review-r04i/README.md) compares 148 unique
power-related pins between a fresh native schematic export and the saved PCB.
It reproduces three open findings: no guaranteed modem undervoltage margin,
uncontrolled GPIO supply sequencing, and a battery-divider feed path when GPIO
power is absent. The calculations are illustrative; no powered failure or repair
is claimed. Nominal charger settings are 4.2 V / 500 mA input / 100 mA charging.

`python3 scripts/audit_power_architecture.py` reproduces the evidence and returns
exit code 2 for electrical HOLD. Standard handoff verification checks this report
as well as the unchanged PCB/mechanical artifacts; its evidence PASS is not
electrical acceptance. The tested Gerber and mechanical bundle remain unchanged.

The [Türkiye connectivity review](turkiye-connectivity.md) identifies manufacturer
Vodafone certification coverage and a firsthand local-SIM connection report.
Neither establishes this collar's activated service or moving-device performance.
Keep nRF9151 as the prototype candidate; verify a local subscription and both
radio modes on a development kit before production antenna/pack release.

## Active mechanical work

The user selected swimming / an IP68 design target. The provisional condition is
2 m fresh water for 60 minutes; depth/time and magnetic charging remain engineering
assumptions pending the user's preference replies.

`mechanical/swim-r02-fit/` is the preserved r04i populated-board fit revision. It retains
the shell, lid, lift-out carrier, independently sealed charging targets, magnet
plugs, dock alignment shell and required TPU boot. Rigid size remains
57.4 × 49.4 × 17.6 mm, 58.7 mm including the key; boot 60.4 × 52.4 × 22.4 mm.

The actual native placements now have 49 drawing-derived component-height
envelopes, two factory wire-termination requirements and two bare test-pad areas;
C11/C12 remain DNP. Maximum height including solder/warp allowances is 2.75 mm
above and 1.75 mm below the board. All 53 entries pass the declared fit screen;
the narrowest component gap is C10 to the carrier, 0.24 mm against a 0.20 mm target.
These are dimensional screens, not component or PCBA purchasing approval.

D1's tolerance envelope required a local carrier relief. The original M4 backing
hardware envelope failed floor/board clearance; r02 uses a dimensional M3 thin-nut
candidate, a 3.5 mm M3 × 0.5 contact thread and Z=5.5 mm contact centers. Two shallow
carrier reliefs clear the backing stack while retaining 1 mm connecting bridges.
The terminal/washer stack is still a constrained reservation, not a selected harness.

Six regressions pass, including the original interference cases and an oversized
J4 wire termination. An independent CAD boolean is empty for the revised geometry
and nonempty when the original carrier is restored. All eight exported meshes
are closed, oriented and connected; four previews and both review sheets were
inspected. The 30 inherited shell/seal checks also pass. r01 and its bundle remain
byte-preserved.

This is a **prototype, not a completed production design**. The
[selection review](../mechanical/swim-r02-fit/selection-review.md) explains why the
researched protected packs and antennas are not yet released: size alone does not
prove modem pulse capability or RF performance. The 30 × 5 mm antenna rectangles
still represent reservations. Dock electronics, harness routing/strain relief,
positive PCB retention, material/seal grades, actual lid fasteners and torque remain
open. No physical ingress, powered or RF result exists.

The active `mechanical/swim-r05-route-fit/` preliminary screen uses actual r05f
placements and 71 profiles, including two DNP parts. All 69 populated envelopes
and 30 analytical shell checks pass. C9's new position clears the carrier; the
smallest gap remains C10/carrier at 0.24 mm. Nine resistor-height envelopes remain
component requirements. The original carrier control still detects D1 interference.
Top/bottom PCB and populated previews were inspected. r02's mesh/boolean acceptance
and release bundle do not transfer; no new mesh package or physical test is claimed.
The earlier r03 and r04 fit checkpoints remain preserved with their own PCB hashes.
