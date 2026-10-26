# r05m / PCBA r03 — Q1 sourced, first SMT results

Q1 is now **ROHM UM6K34NTCN / C510056**. The next prototype uses the same
copper, nets, lands and Gerber as r05l. Fresh native DRC, ERC and schematic
parity pass. JLC matches all **44 MPNs / 81 fitted references** and its downloaded
placements reproduce every supplied coordinate, side and angle.

**PCBA order release is still HOLD.** The first actual SMT analysis has findings;
the SIM socket is still a visual placeholder. These are not all-green SMT files.

| File | Use |
|---|---|
| [bom.csv](bom.csv) | Current exact parts; replaces r01 BOM only for this revision |
| [cpl-jlc-review.csv](cpl-jlc-review.csv) | JLC model coordinates; Q1 rotation 270 degrees |
| [Native project](../../experiments/pcba-r05m-rohm-q1/hardware/collar-tracker.kicad_pro) | Current Q1 metadata; geometry unchanged |
| [Gerber ZIP](../../experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip) | Same verified manufacturing bytes as r05l |
| [Placement reference](placement-reference.svg) | Native physical centres, pins, nets and SIM insertion direction |
| [SMT report](smt-report.pdf) | Actual supplier report, including unresolved findings |
| [SMT disposition](smt-disposition.md) | What the measurements establish and what remains open |

## Q1 selection

[ROHM's datasheet](https://fscdn.rohm.com/en/products/databook/datasheet/discrete/transistor/mosfet/um6k34ntcn-e.pdf)
specifies the required six-pin arrangement and low-voltage operation.
The part pulls down U4 enable and discharges the external 1.8 V rail through
22 ohms; it does not carry modem supply current. At 25 C, maximum RDS(on) is
2.8 ohms at 1.5 V / 200 mA. VDS 50 V and VGS +/-8 V exceed this circuit's
5.5 V maximum rail. The former Diodes 60 V / +/-20 V ratings are not retained.

Including the resistor's initial tolerance and TCR over -40..85 C gives an
87.81 mA initial current bound and 21.66 uJ capacitor energy. A resistance-independent
screen bounds the two FETs' combined dissipation at 42.48 mW. The reference-land
thermal comparison passes at 85 C; it is not a measured board-temperature result.
The 800 mA / 10 us pulse rating is not used. Hot RDS, falling-rail behavior and
actual powered operation remain first-prototype tests.
See the calculations, limitations and source hashes in [q1-review.json](q1-review.json).

The live JLC search showed **828 units at 09:12 UTC, 26 October 2026**
([capture](previews/q1-stock.png)). Stock is unreserved and must be checked at ordering.
The alternate Diodes DMN62D0UDWQ-13 had zero JLC assembly stock in this session
and was not selected. No other BOM substitution was made.

ROHM pin 3 is D2 and pin 6 is D1, matching the existing native symbol.
The old r02 drawing/report reversed those channel names; its electrical net
mapping was unchanged because both sources and gates are common. The current
placement drawing corrects the names and identifies the selected ROHM part.

## Placement and evidence

Q1 keeps its physical centre (34, 6.75) mm and native angle 90 degrees. The
supplier library needs 270 degrees to map all six numbered lands correctly.
Its row-centre difference is about 0.05 mm; native lands are unchanged.
The thirteen r01 angle corrections and r02 U.FL origin offsets are retained.
J1/J2 supplier X coordinates are 0.6320028 mm left of their physical centres;
do not treat this supplier model datum as a universal machine datum.

[Supplier read-back](jlc-preview-positions.json) verifies 58 top and 23 bottom
references, all 44 exact MPNs and no omitted part. The downloaded BOM and CPL
are byte-identical to the local files. Both [top](previews/top.png) and
[bottom](previews/bottom.png) previews were inspected. Save & Close synchronized
the DFM inputs; it was not a purchase or factory release.

J6 remains the exact no-peg GCT SIM8051-6-0-14-00-A / C7363812. All eight native
lands/functions and insertion direction were compared with the manufacturer
D6 drawing in [r02](../pcba-r02/connector-review.json). The actual SMT backend
now reports J6 body spacing, so the missing visual model does not mean the
backend has no geometry. However, no explicit J6 pin-overlap/model-validation
evidence was returned. Complete socket assembly acceptance is still open.

[Native checks](native-checks.json) retain the inherited five disabled DRC and
four disabled ERC categories. None was changed. Exact inverse text substitutions
recover every copied r05l native file; geometry, ground planes, returns and rules
are unchanged. The two saved PCB-only DFM passes apply to identical Gerber bytes.
No fresh all-green PCB claim is made for the renamed source.

Next: resolve the SMT pin/stencil discrepancies and complete J6 model/manual
placement acceptance. Do not restart firmware or mechanical work. Supplier
messaging is set aside at the user's request; no enquiry or order was sent.

Run `python3 scripts/verify_pcba_r03.py` for read-only source, BOM/CPL, supplier
read-back and package checks. It verifies saved evidence, not factory acceptance.
