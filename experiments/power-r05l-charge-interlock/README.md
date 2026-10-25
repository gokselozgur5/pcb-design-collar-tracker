# r05l — hardware charge interlock

This revision implements the cell-temperature charge window on the PCB and
preserves the tested r05k source. Native DRC/ERC/connectivity/parity have zero
findings. Two actual JLC PCB analyses of the final ZIP each report
**0 Danger / 0 Warning / 455 Good**, with all 29 rows analyzed and unchanged rules.

[Gerber ZIP](evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip) ·
[JLC report 1](evidence/jlc-check1/report.pdf) ·
[JLC report 2](evidence/jlc-check2/report.pdf) ·
[Candidate BOM](assembly/candidate-bom.csv) · [Candidate CPL](assembly/candidate-cpl.csv)

| Identity | Value |
|---|---|
| PCB | 40 × 32mm; six copper layers; 87 footprints |
| Fitted parts | 81 references / 44 exact candidate MPNs |
| PCB SHA256 | `241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3` |
| Gerber SHA256 | `c736c5d35ddfe4c4662e57606120f00f7358492e11d5fbb32eaf1d0ff6caf5d2` |
| Supplier records | `637366592129687553`, `637366801595977730` |
| GND | Two dedicated planes; 109 physical GND pads with local via paths; 122 GND vias |
| Return screen | All 154 signal vias within the inherited 2mm screen |
| Electrical / RF / assembled release | HOLD; no powered or physical qualification |

U3 /CE is now driven by a NAND of two VSYS-powered comparator permissions.
The new circuit handles steady-state hot, cold, open-sensor and short-sensor
conditions independently of the MCU. The [charge review](../../assembly/charge-interlock-r01/README.md)
records exact parts, manufacturer sources, conditional temperature bounds and
remaining startup/thermal measurements. A protected pack and sensor attachment
are still needed. Do not interpret a model PASS as battery-system qualification.

All original footprints/lands and 27 RF segments remain unchanged. Routing changes
are limited to the new circuit, its supply/sensor connections and the local VIN
escape. The source comparison and native inventories bind these claims to the
final PCB. The inherited stack is JLC06081H-7628, nominal 0.8mm class with
0.84088mm explicit CAD thickness including mask.

The first real supplier run reported 3 Danger / 4 Warning. Moving three full-size
labels and relocating one VIN via resolved them. A subsequent native check caught
insufficient clearance to VBAT, so the via also moved 0.05mm left before the final
export. Failed native and supplier evidence remains preserved. No supplier/native
rule was weakened and no manufacturing land was reduced.

The [r07 carrier](../../mechanical/swim-r07-charge-interlock/README.md) clears the new
bottom-side NAND with one ledge relief and one shifted support leg. All 85 fitted
envelopes pass four thickness scenarios; the previous carrier still fails the
negative control. Shell/seal/contact dimensions remain unchanged. The pack and
antennas are still reserved volumes. IP68 is a design target, provisionally
2m fresh water for 60 minutes; there is no physical water/dust qualification.

`python3 scripts/verify_charge_candidate.py` checks the saved evidence without
changing CAD or contacting services. Saved native files are authoritative;
one-shot seed/routing scripts are engineering history, not an instruction to
overwrite this revision. Preserve this source and use a successor for further edits.

Next: select a protected pack, NTC attachment and actual LTE/GNSS antennas; complete
harness/dock/retention definitions, firmware and factory programming/test.
Supplier procurement, CPL rotations, stencil/reflow/SMT, powered operation, RF and
ingress qualification are still open. This is a PCB review package, not a fully
working-PCBA order release.
