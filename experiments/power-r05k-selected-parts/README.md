# r05k — selected component candidate

This successor applies four reviewed value changes and exact candidate MPNs for
all 65 fitted components. The 40 × 32 mm six-layer routing, placements, lands,
vias, fills, stack and rules remain structurally identical to tested r05j.
The board legend changes to `CT 0.5K`. Preserved r05j is untouched.

[Gerber ZIP](evidence/collar-tracker-05k-parts-40x32-dfm.zip) ·
[JLC report 1](evidence/jlc-check1/report.pdf) ·
[JLC report 2](evidence/jlc-check2/report.pdf) ·
[Candidate BOM](assembly/candidate-bom.csv) ·
[Candidate CPL](assembly/candidate-cpl.csv)

| Check | Result |
|---|---|
| PCB SHA256 | `bea6c52a7f045b5fb21ac9714f3db0c70207f150aab3e9587b891f08e4e2b4d3` |
| ZIP SHA256 | `673c1d30bf2192f8abe60cf211ac183210472b8924f3fd4c3b5b46bd992412fc` |
| Native DRC / ERC / opens / parity | Zero findings |
| JLC PCB records | `637356580811132930` / `637356797304328193` |
| Each JLC result | 0 Danger / 0 Warning / 450 Good; 29 analyzed rows; unchanged rules; SMT off |
| Circuit topology | All original r05 native nets unchanged |
| Value changes | R17 200 kΩ; R18 26.1 kΩ; R19 3.4 MΩ; C25 1 µF / 16 V X7R |
| Assembly candidates | 65 fitted references / 38 unique exact MPNs |
| Populated fit | 69 envelopes pass at 0.71 / 0.81 / 0.84088 / 0.91 mm; original carrier still fails |
| Resistor height reservations | All nine replaced by selected manufacturer dimensions |
| Purchasing / powered / RF / ingress | Not accepted |

Both complete supplier PDFs were rendered and inspected. Raw measurements, UI
rows, rules and upload receipts agree with each other and the same final ZIP.
PCB DFM proves only the analyzed manufacturing geometry.

The [component review](../../assembly/power-parts-r01/README.md) explains the
manufacturer sources, leakage/TCR calculations, increased C25 delay, additional
divider consumption and remaining physical assumptions. The exact code, BOM,
schematic and native PCB fields agree. Other passive MPNs are promoted from the
existing drawing-based mechanical candidates; that does not establish their
electrical, lifecycle, availability or supplier-assembly acceptance.

The [assembly receipt](assembly/assembly-check.json) binds the native position
export to 65 CPL rows. C11/C12 remain DNP. J3/J4 are factory wire-termination
interfaces; J5/J7 are bare contacts, so none is an SMT placement. External pack,
NTC, antennas, harness, dock and fixture hardware remain in the product scope.
The CPL uses KiCad's placement origin, X right / Y up, no bottom-X negation, and
angles modulo 360. Supplier library rotations and solder process still require
acceptance. No PCB/PCBA order or quote request has been submitted.

The r05j ground returns, R3 balance, RF-reference coverage and SIM access are
inherited through whole-structure equality, with fresh native DRC and geometry
exports. This does not transfer physical RF qualification that never existed.
The populated-fit check uses the actual new heights, including C25's 1.35 mm body;
its limiting gap is 0.60 mm to the existing battery reservation. No physical
water/dust or full harness/antenna fit is claimed.

## Verify and continue

```sh
python3 scripts/verify_selected_parts.py
python3 scripts/check_power_parts.py
python3 scripts/verify_handoff.py
```

`evidence/parts-checkpoint.json` enumerates the public candidate files. Native
exports require the matching project, the documented KiCad installation and a
single LoadBoard per process. The seed is a one-shot provenance tool, not a
command to rerun over this saved source.

Next: select the protected NTC pack and actual LTE/GNSS antennas against pulse
capability and the populated enclosure, then finish harness/dock/retention,
firmware and factory programming/test instructions. Review the new conditional
power inputs during bring-up; do not repeat routing/DFM without a real change.
