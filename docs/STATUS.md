# Current state — 2026-10-25

**Active r05j RF junction candidate: native DRC/ERC/parity clean; two actual JLC PCB runs at 0 Danger / 0 Warning.**
**Electrical / RF / manufacturing release: HOLD. IP68 remains unqualified.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All authored repository/GitHub content is English. Continue from
`experiments/power-r05j-rf-junctions/hardware/`; preserve this tested source before changing it.

[Gerber ZIP](../experiments/power-r05j-rf-junctions/evidence/collar-tracker-05j-rf-40x32-dfm.zip) ·
[Before / after review](../experiments/power-r05j-rf-junctions/evidence/rf-junction-review.pdf) ·
[JLC report 1](../experiments/power-r05j-rf-junctions/evidence/jlc-check1/report.pdf) ·
[JLC report 2](../experiments/power-r05j-rf-junctions/evidence/jlc-check2/report.pdf)

## Active r05j layout

PCB SHA256: `51fc05ccc66009995daa8c5d5466aa983436e00e7ff338f0ddfb0927c92b4580`.
ZIP SHA256: `8fd625d3da7b8bd3c59ea9aa0fd625dc93d458fe23b64a6fd7bc69d4c6915e50`.

| Check | Result |
|---|---|
| Size / circuit | 40 × 32 mm, six Cu, unchanged 71-part r05 circuit |
| Stack candidate | JLC06081H-7628, nominal 0.8 mm class; explicit CAD including mask 0.84088 mm |
| Native DRC / ERC / parity | Zero violations, warnings, opens or mismatches |
| Ground / returns | 94 unique GND terminals local; 110 GND vias; two continuous GND planes; 128/128 return screens pass |
| RF change | R3 moves 0.30 mm, one 0.36 mm entry per land; C11 branch shortened; C12 branch removed |
| R3 copper ratios | 2.288 / 2.413 / 2.090 → 1.004 / 1.003 / 1.001 at the three review contours |
| RF reference | 1,742 native probes agree; entire RF track projection backed by In1.Cu |
| Unchanged geometry | All other placements, lands, vias, non-LTE routes, inner copper, planes and DRC limits |
| JLC PCB DFM | `637352328236847105` and `637352583225630721`; 29 rows / 450 green measurements each; same ZIP/rules; SMT off |
| Mechanical | 69 populated envelopes pass at 0.71 / 0.81 / 0.84088 / 0.91 mm; old carrier still fails |

Read the [r05j decisions and limits](../experiments/power-r05j-rf-junctions/README.md).
The main LTE feed length grows from 5.89 to 8.91 mm while reducing tuning stubs.
This is a copper-balance improvement, not a measured RF improvement. The inherited
0.36 mm width remains a prototype candidate: the supplier's Er/etch/mask and
finished-thickness conventions still differ. In1.Cu remains under the module RF
pads to avoid exposing lower VBAT; transition qualification remains open.

**Next local work:** select exact R1/R16–R23 MPN/tolerance/TCR and qualify effective
C9/C25/C26 bounds in the power model. Do not start another routing revision merely
to repeat green checks. Then finish battery/NTC, antenna and factory BOM/CPL/
programming/test definitions. Preserve the reference and resolve stack/process
parameters before claiming controlled impedance. Review the
[sequencing follow-up](power-sequence-followup.md) before changing the circuit.
Complete retention/harness/dock/seal selection and physical water/dust qualification.

PCB DFM is complete for the delivered bytes. Do not order this as a finished working
PCBA yet. Every subsequent PCB edit needs fresh native checks/export/two supplier runs.
`python3 scripts/resume.py` verifies saved evidence; it does not repeat physical tests.

The preceding [r05i](../experiments/power-r05i-rf-stack/README.md),
[r05h](../experiments/power-r05h-six-layer/README.md) and earlier releases remain
immutable. SIM protection and the bottom-side card lane are inherited through
unchanged copper and placement; all 12 original power backbones remain connected.

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

The active `mechanical/swim-r06-six-layer-fit/` uses the actual r05h PCB and
nominal 0.8 mm thickness. All 69 populated envelopes and 30 shell checks pass;
the smallest checked gap is C10/carrier at 0.24 mm. Nine resistor-height limits
remain component requirements. Actual supplier stack/thickness tolerances,
positive retention and physical tests remain open. The inspected preview is a
conservative volume model; r02 mesh acceptance does not transfer automatically.
