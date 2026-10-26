# r05l PCB assembly review

**Review files, not an order release.** This package covers the unchanged
40 x 32mm, six-copper-layer r05l PCB. It contains 81 fitted references and 44
exact manufacturer part numbers: 58 placements on top and 23 on bottom.
The two saved PCB DFM results remain 0 Danger / 0 Warning / 455 Good each.
Those results did not include SMT analysis.

| File | Purpose |
|---|---|
| [bom.csv](bom.csv) | Grouped exact MPN, designators, physical package and quantity |
| [cpl.csv](cpl.csv) | Native component centres, rotations and assembly side |
| [cpl-jlc-review.csv](cpl-jlc-review.csv) | Supplier review candidate with 13 IC/discrete rotation corrections |
| [file-checks.json](file-checks.json) | Source/output hashes, reference counts and origin check |
| [interface-pads.csv](interface-pads.csv) | All 23 bare charging, battery, expansion and programming lands |
| [pin-one.csv](pin-one.csv) | Native pin-1 lands for 18 fitted ICs/discretes/connectors |
| [fitted-pads.csv](fitted-pads.csv) | Native fitted-part pad geometry, including unnumbered paste apertures |
| [contact-export.json](contact-export.json) | Read-only KiCad export identity and limits |
| [jlc-reviewed-match.json](jlc-reviewed-match.json) | Actual final-file match: 43 exact MPNs, Q1 unmatched |
| [orientation-review.json](orientation-review.json) | Numbered-land comparison and unresolved library models |

## Actual supplier review

On 2026-10-26, JLC matched 43 of the 44 exact MPNs. Q1 `DMN62D2UDW-7`
remains unmatched, including a manual search for the exact base part. A broader
search returned other parts, which were not selected as substitutes. The final
review-CPL upload has SHA-256
`46f4a72547b5607c65bfd7fb53e33b2f65f599997b18a1b7e72a21b5cbf5f01e`;
the browser's uploaded-file digest matched the local bytes. Library matching is
not stock reservation, purchasing acceptance or SMT approval.

The initial preview contained only 80 mounted references (57 top, 23 bottom):
JLC left out unmatched Q1. It also exposed rotation differences between native
KiCad and JLC library coordinates. The supplier review CPL changes only these
13 rotations; all centres, assembly sides, references and the PCB are preserved:

| References | Native angle | Supplier review angle |
|---|---:|---:|
| D1, D2 | 0 | 90 |
| U2 | 180 | 90 |
| U3, U4, U5 | 0 | 270 |
| U6, U8 | 0 | 180 |
| U7, U12 | 90 | 270 |
| U9 | 270 | 180 |
| U10, U11 | 90 | 0 |

U1 retains 0 degrees. The comparison uses all matching numbered lands, including
exposed pads, on these 14 IC/discrete references. It selects among four cardinal
angles and records every score. Library land centres differ from native lands
by up to 0.26mm after orientation; this comparison establishes pin order/orientation,
not equivalence of the stencil, solder lands or assembly process.

After reloading the supplier page, its downloaded preview data reproduced all
80 available centres, sides and corrected angles exactly; Q1 was the only missing
reference. The sanitized [read-back](jlc-preview-positions.json) records that result.
The initial [top](previews/native-top.png)/[bottom](previews/native-bottom.png)
and corrected [top](previews/reviewed-top.png)/[bottom](previews/reviewed-bottom.png)
previews were inspected. Pin-1 directions agree with the corrected IC/discrete
mapping on both sides. The preview does not resolve the four open references or
constitute a complete SMT run. No placement-approval/order submission was made.

Q1 has no exact match. J6 matches its exact MPN but has no footprint/model in the
returned library data. J1/J2 have different library pad numbering, origin and land
arrangement and need a manufacturer/package review. These four references remain
explicitly open. Do not approve an 80-part preview as the complete 81-part board.

The library comparison uses the [JLCEDA](https://lceda.cn/)/
[EasyEDA Official Library](https://easyeda.com/) and its
[documented coordinate units](https://docs.easyeda.com/en/API/2-Coordinate-System-and-Unit/).
The dated response hashes are recorded without publishing customer/session data.

## Files and coordinates

Use the exact existing
[Gerber ZIP](../../experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip),
SHA-256 `c736c5d35ddfe4c4662e57606120f00f7358492e11d5fbb32eaf1d0ff6caf5d2`.
The native PCB SHA-256 is
`241c84d6ba98793c37344e1e46ddc4918e7b05322ba87daea7c9a90ffb8379b3`.
JLC06081H-7628 is the stack candidate; nominal 0.8mm class, 0.84088mm in CAD.

All coordinates are millimetres, X right and Y up in the Gerber top view.
Top and bottom use the same origin; the bottom coordinates are **not mirrored**.
The native auxiliary origin is (100, 128)mm. The actual Gerber board boundary
is X = -2..38mm and Y = -2..30mm. Negative placements within that boundary
are intentional. Do not recenter only one of the Gerber/CPL files.

The baseline `cpl.csv` retains native KiCad angles modulo 360; use
`cpl-jlc-review.csv` for the next supplier review. Full placement acceptance is
still open. Inspect pin 1, polarity and connector
entry direction on both sides using the native board and the supplied pin table.
A pin-1 land export is a placement reference, not a supplier rotation approval.
The pad-size columns are local pad X/Y dimensions; pad rotation is recorded
separately. Bottom placement must be checked in the supplier's displayed view.

C11 and C12 are deliberately DNP. J3/J4/J5/J7 are bare contact patterns with
no component to place, so they are excluded from the SMT BOM/CPL. Nothing else
may be omitted to obtain an assembly pass. In particular, an unmatched Q1
must not become DNP.

## External assembly and programming

| Interface | Pin assignment | Remaining factory responsibility |
|---|---|---|
| J3, top | 1 VIN_5V; 2 GND | Attach and inspect charging harness |
| J4, bottom | 1 VBAT; 2 GND; 3 BAT_NTC | Approved protected pack and controlled sensor/harness attachment |
| J7, bottom | 1 VIO_1V8; 2 SWDIO; 3 GND; 4 SWDCLK; 5 DEBUG_RESET; 6 VSYS | Fixture/contact access, programming and verification |
| J5, bottom | Full net mapping in interface-pads.csv | Optional digital expansion, no heart-rate sensor fitted |
| J1/J2, top | LTE / GNSS U.FL | Fit selected antenna/cable assemblies and verify RF performance |
| J6, bottom | Physical nano-SIM socket | SIM insertion/access and service qualification |

J7's VIO contact is the 1.8V logic reference; do not connect a 3.3V probe drive
to these logic pins. Fixture power sequencing, loading and contact mechanics
remain unqualified. The protected battery is still a requested envelope, not
an approved supplier part. Factory harness assembly must not be passed back
to the owner as soldering work.

[Factory observation firmware](../../firmware/README.md) and the
[signed tracker r03 prototype](../../firmware/tracker-r03/README.md) have built
for the target. No board has been flashed. Production programming requires an
explicitly approved image, key/provisioning procedure and recorded powered tests;
the development-signed tracker image is not a production programming release.

## Evidence boundaries

CSV preparation checks exact source hashes, reference sets, sides, native centres,
angles and the actual Gerber outline. The contact exporter loads the native PCB
once and does not save it. Neither operation changes PCB acceptance evidence.
Library matching, purchasing availability, placement review, SMT analysis,
stencil/reflow approval and powered testing are separate gates.

Formatting follows JLC's
[BOM requirements](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly),
[KiCad import guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)
and [matching guidance](https://jlcpcb.com/help/article/common-bom-and-cpl-matching-issues-and-explanations).
Supplier inventory and library results are dated observations, not procurement
commitments. No order, payment or supplier message is authorized by this package.
