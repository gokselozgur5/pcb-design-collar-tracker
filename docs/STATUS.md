# Current state — 2026-10-25

**Active r05k selected-component PCB: native DRC/ERC/parity clean; two actual JLC PCB runs at 0 Danger / 0 Warning.**
**Electrical / RF / manufacturing release: HOLD. IP68 remains unqualified.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All authored repository/GitHub content is English. Continue from
`experiments/power-r05k-selected-parts/hardware/`; preserve the tested source before changing it.

[Gerber ZIP](../experiments/power-r05k-selected-parts/evidence/collar-tracker-05k-parts-40x32-dfm.zip) ·
[JLC report 1](../experiments/power-r05k-selected-parts/evidence/jlc-check1/report.pdf) ·
[JLC report 2](../experiments/power-r05k-selected-parts/evidence/jlc-check2/report.pdf) ·
[Candidate BOM](../experiments/power-r05k-selected-parts/assembly/candidate-bom.csv) ·
[Candidate CPL](../experiments/power-r05k-selected-parts/assembly/candidate-cpl.csv)

[Current review PDF](../release/r05k-review/review.pdf) ·
[PCB review bundle](../release/collar-tracker-r05k-pcb-review.zip)

**New charge-temperature finding:** the direct 10k/B3435 NTC option permits
charging at 50°C, above the reviewed candidate pack's 45°C maximum. U3 /CE is
tied to GND, so firmware alone cannot repair this source. The charge interlock
is not implemented. See the [source-bound battery review](../assembly/pack-charge-r01/README.md).
The candidate EEMB pack is also limited to 350mA continuous by its PCM despite
its 700mA bare-cell rating. No pack or NTC has been selected.

## Active r05k layout and parts

PCB SHA256: `bea6c52a7f045b5fb21ac9714f3db0c70207f150aab3e9587b891f08e4e2b4d3`.
ZIP SHA256: `673c1d30bf2192f8abe60cf211ac183210472b8924f3fd4c3b5b46bd992412fc`.

| Check | Result |
|---|---|
| Size / topology | 40 × 32 mm, six Cu, unchanged 71-footprint r05 topology |
| Stack candidate | JLC06081H-7628, nominal 0.8 mm class; explicit CAD including mask 0.84088 mm |
| Native DRC / ERC / parity | Zero violations, warnings, opens or mismatches |
| Copper / placement | Entire saved structure identical to r05j except value/MPN/status fields and revision label |
| Ground / returns | Inherited 94 local GND terminals, 110 GND vias, two dedicated GND planes, 128/128 return screens |
| Values | R17 200 kΩ; R18 26.1 kΩ; R19 3.4 MΩ; C25 1 µF / 16 V X7R |
| Exact candidate MPNs | 65 fitted references / 38 unique parts; candidate BOM/CPL exported |
| Component analysis | Tolerance/TCR/leakage and typical-capacitance screens pass with explicit remaining assumptions |
| JLC PCB DFM | `637356580811132930` / `637356797304328193`; 29 rows / 450 green measurements each; same ZIP/rules; SMT off |
| Mechanical | 69 populated envelopes pass at 0.71 / 0.81 / 0.84088 / 0.91 mm; all nine resistor heights now sourced |

Read the [r05k decisions and limits](../experiments/power-r05k-selected-parts/README.md)
and [component review](../assembly/power-parts-r01/README.md). The manufacturer-listed
lower-impedance divider adds a nominal 13.39 µA at 3.6 V. C25 replaces an NRND part
with the in-production C9 MPN; its modeled reset delay is 2.057–10.121 s. Its increased
height still leaves 0.60 mm to the battery reservation. No powered behavior is claimed.

The component model includes −40..85°C TCR, both PG leakage signs, RESET sink current,
a 0.5% additional resistance-drift sensitivity and typical Murata small-signal curves.
The provisional firmware wait is 1 s; the former 600 ms fails the model. Effective
capacitance, timer scaling, drift and fast collapse still need assembled validation.
UVLO leaves pull-up current flowing; protected-cell cutoff/recharge behavior matters.

**Next local work:** implement a cell-temperature charge interlock that remains
effective during boot, reset, low-cell recovery and sensor faults. Select the
protected pack/NTC against the full pack current and charge limits, then select
the actual LTE/GNSS antennas and check their occupied volumes. Complete
harness/dock/positive retention/seal definitions, firmware, programming and factory
functional test. The 65 fitted MPNs are candidates, not supplier procurement or SMT
acceptance; check their electrical suitability, availability and CPL library rotations.
Do not reroute or repeat DFM without a real source change. Review the
[sequencing exception](power-sequence-followup.md) before adding retention hardware.

The inherited RF route uses 0.36 mm main feeds; R3 has one equal-width land entry
and 1.001–1.004 contour ratios. Supplier Er/etch/mask/thickness differences, module
transitions, actual antennas and physical RF acceptance remain open. In1.Cu remains
under module RF pads to avoid exposing underlying VBAT. See the preserved
[r05j RF review](../experiments/power-r05j-rf-junctions/README.md).

PCB DFM is complete for the delivered bytes. This is not a finished working-PCBA
order package. Subsequent PCB edits need fresh native/export/two supplier checks.
`python3 scripts/resume.py` verifies saved evidence without repeating physical tests.
All previous r05j/r05i/r05h and earlier tested sources remain immutable.

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

The preserved `mechanical/swim-r06-six-layer-fit/` uses the r05h PCB and
nominal 0.8 mm thickness. All 69 populated envelopes and 30 shell checks pass;
the smallest checked gap is C10/carrier at 0.24 mm. Nine resistor-height limits
remain component requirements in that snapshot. The r05k fit profile replaces them
with sourced heights and also checks the larger C25; its 69 envelopes pass. Actual supplier stack/thickness tolerances,
positive retention and physical tests remain open. The inspected preview is a
conservative volume model; r02 mesh acceptance does not transfer automatically.
