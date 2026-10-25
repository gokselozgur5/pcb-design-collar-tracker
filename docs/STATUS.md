# Current state — 2026-10-26

**Active r05l: hardware charge-temperature interlock implemented; native DRC/ERC/parity clean; two actual JLC PCB runs at 0 Danger / 0 Warning / 455 Good each.**
**Working-device / RF / manufacturing release: HOLD. IP68 remains unqualified.**

Continue from `experiments/power-r05l-charge-interlock/hardware/`.
The preserved r05k and earlier sources remain immutable. All authored repository/GitHub
content is English. Run `python3 scripts/resume.py` before making another revision.

[Gerber ZIP](../experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip) ·
[JLC report 1](../experiments/power-r05l-charge-interlock/evidence/jlc-check1/report.pdf) ·
[JLC report 2](../experiments/power-r05l-charge-interlock/evidence/jlc-check2/report.pdf) ·
[Two-page review](../release/r08-assembly-review/review.pdf) ·
[Review bundle](../release/collar-tracker-r05l-r08-review.zip)

| Check | Current result |
|---|---|
| Board | 40 × 32mm; six Cu layers; 87 footprints |
| Assembly candidates | 81 fitted references / 44 exact MPNs; BOM/CPL exported |
| Native DRC / ERC / opens / parity | Zero findings |
| Charge circuit | Two VSYS-powered TLV3012B comparators and SN74LVC1G00 NAND drive /CE independently of MCU/VIO |
| Temperature model | Conditional pass; nominal 6.29–36.21°C sensor window; original 50°C case disabled |
| Original source preservation | 71 footprints/lands, 27 RF segments, stack, rules and keepouts unchanged; only U3.4 original pin changes net |
| Local routing | New charge nets and supply/sensor branches; local VIN escape rerouted |
| Ground / returns | 109 physical GND pads have local via paths; 122 GND vias; two dedicated planes; 154/154 signal-via return screens |
| JLC PCB DFM | Records `637366592129687553` / `637366801595977730`; same ZIP/rules; 29 rows; SMT off |
| Mechanical r08 | 85 populated envelopes pass four thickness cases; eight closed meshes; current CAD intersections empty, old carrier and undersized cable guides rejected |
| Antenna candidates | Synzen CAPH SZK-C-3L30 LTE and ZETA SZK-C-0G04 GNSS; separate nominal 100mm cable assemblies and four internal lid guides |

PCB SHA256: `241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3`.
Gerber SHA256: `c736c5d35ddfe4c4662e57606120f00f7358492e11d5fbb32eaf1d0ff6caf5d2`.
Stack candidate: JLC06081H-7628, nominal 0.8mm class, explicit CAD thickness 0.84088mm.
In1/In4 are dedicated GND planes; F/In2/In3/B carry signals.

Read the [r05l evidence](../experiments/power-r05l-charge-interlock/README.md),
[charge review](../assembly/charge-interlock-r01/README.md) and
[r08 antenna enclosure](../mechanical/swim-r08-antennas/README.md).
The first supplier run failed 3 Danger / 4 Warning; full-size label moves and a
VIN-via relocation fixed them without weakening rules or shrinking lands.
The final ZIP passed two fresh analyses. Preserve those exact bytes.

The [r05k battery finding](../assembly/pack-charge-r01/README.md) remains historical
evidence: that source grounded /CE and permitted 50°C charging with a direct
10k/B3435 sensor. The new source implements the interlock. SEMITEC 103JT-025 is a
candidate sensor; no protected pack or factory cell attachment is selected.
The reviewed EEMB PCM supports 350mA continuous despite its 700mA bare-cell rating.

**Next local work:** bound the modem's actual pulse and duty-cycle load, then select
a protected pack and NTC attachment against complete-pack protection, voltage and
charging limits. The 600mA continuous screen was engineering headroom, not a Nordic
continuous-load requirement; Nordic describes approximately 500mA peak at 3.7V.
Do not reject a small pack solely for missing that continuous-current screen, or
accept it from average current alone. The [selection review](../assembly/pack-antenna-r02/README.md)
records the primary sources and conditional candidates. Close cable end-datum,
length-tolerance and feed-bond definitions, then harness/dock/positive PCB retention,
material/seal/fastener definitions and firmware/factory test. Do not
reroute or repeat DFM without a real source change. For a PCB edit, create a
successor and rerun native/export/two actual supplier checks.

Charge bounds depend on sensor R/T and full-temperature leakage assumptions and a
2°C cell-to-sensor allocation including lag. Startup, brownout, low-cell recovery,
sensor-insertion transients, actual current and thermal coupling require assembled
measurements. The prior component-selection model still requires a provisional
1s firmware VIO wait; 600ms fails that model. Review the
[sequencing exception](power-sequence-followup.md) before adding hardware.
Supplier procurement, CPL rotations, SMT/reflow, actual stack/impedance and RF
qualification remain open. A conditional calculation is not an electrical release.

IP68 swimming/dust resistance is the design target; 2m fresh water / 60 minutes
and magnetic charging remain engineering assumptions. r08 retains the r07 U12
carrier relief and shifts neither the PCB nor the contact/seal geometry. The taller
shell accommodates the two cable layers: rigid envelope 57.4 × 49.4 × 20.6mm,
excluding the 1.3mm docking key; boot 60.4 × 52.4 × 25.4mm. A 20mm M2 screw
candidate and blind boot pockets replace the former length assumption. Exact
fastener tolerance, torque, clip strength and lid-opening motion are unqualified.
The battery remains a 34 × 23.5 × 5.8mm reservation; the antennas have sourced
candidate dimensions with explicitly provisional cable/placement allowances.
No physical water/dust, powered or RF result exists. This is not yet a complete
working-PCBA order package.

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

## Preserved mechanical baselines

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
