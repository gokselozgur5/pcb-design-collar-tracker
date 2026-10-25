# Current state — 2026-10-25

**r04i PCB: native-clean and two actual JLC runs at 0 Danger / 0 Warning.**
**Swimming enclosure: engineering prototype under review; IP68 is not qualified.**

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
All authored repository/GitHub content is English. Original supplier reports retain
their original metadata.

Review: [two-page PDF](../mechanical/swim-r01/review.pdf) and
[124-file bundle](../release/collar-tracker-r04i-swim-r01-review.zip).
Bundle SHA256: `21e3f0573d7cc0b6ef8b13118e3d23182f1fe0f6fd29d14bfad34404460a6805`.
`python3 scripts/verify_handoff.py` verifies the saved PCB, mechanical checks and
every bundled file against the checkout; it performs no new supplier/physical test.

## Current PCB

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

## Active mechanical work

The user selected swimming / an IP68 design target. The provisional condition is
2 m fresh water for 60 minutes; depth/time and magnetic charging remain engineering
assumptions pending the user's preference replies.

`mechanical/swim-r01/` contains the parametric shell, lid, lift-out carrier, two
radially sealed charging targets, magnet plugs, dock alignment shell and TPU boot.
Current rigid body: 57.4 × 49.4 × 17.6 mm; 58.7 mm including the docking key.
With the retention boot: 60.4 × 52.4 × 22.4 mm. The initial smaller gland and contact
groove failed geometric screens; four regression tests retain those cases.
The two-page `review.pdf`, dimensioned drawing and eight exported closed STL
surfaces are ready for review. `checks.json` binds the 30 analytical checks to the
PCB and parameters; `mesh-checks.json` binds the actual mesh/previews to the CAD.

This is a **prototype, not a completed production design**. Component-height,
protected battery and antenna reservations still need approved drawings. The dock's
spring contacts/power circuit, actual fasteners, seal compounds, material/coating,
wire terminations and assembly torque are not qualified. No physical ingress or
powered result exists. Read the mechanical README before continuing.

Next: replace the reserved pack, antennas and component heights with approved
drawings, finish the dock/harness selections and recheck physical fit. Before
tooling or full PCBA release, complete actual
assembly/RF/power review and whole-assembly dust/immersion testing. Türkiye operator
service and moving-animal coverage remain open. Factory assembly/programming/test
is still required; no end-user soldering is intended.

## Preserved checkpoints

0.3.4 and r04g retain their original native files and two supplier reports.
r04h is the last pre-access-repair source; its clean DRC did not establish card
insertion clearance. None of those earlier supplier results is reused for r04i.
Local rejected routing trials stay in ignored working evidence.

Nano-SIM now, eSIM later. J5 is a digital expansion port, not a heart-rate sensor.
No order, payment, supplier message, powered test or production approval occurred.
