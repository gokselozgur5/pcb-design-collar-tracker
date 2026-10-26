COLLAR TRACKER r05m / PCBA r03 — ASSEMBLY REVIEW, NOT ORDER RELEASE

Current PCB source: experiments/pcba-r05m-rohm-q1/hardware/
Change: Q1 is ROHM UM6K34NTCN / JLC C510056. No copper, net, pad or board-size change.

USE TOGETHER:
  assembly/pcba-r03/bom.csv
  assembly/pcba-r03/cpl-jlc-review.csv
  experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip

The Gerber filename remains r05l because its bytes are unchanged:
SHA256 c736c5d35ddfe4c4662e57606120f00f7358492e11d5fbb32eaf1d0ff6caf5d2
The two saved all-green reports cover PCB DFM only.

JLC matched 44/44 MPNs. Actual supplier read-back verifies all 81 fitted references
(58 top, 23 bottom), their exact parts, sides, coordinates and angles. Uploaded
BOM/CPL downloads match the local files byte for byte.

The review CPL uses supplier-specific model origins/angles. Q1 is 270 degrees;
J1/J2 retain the r02 -0.6320028mm X model-origin correction. Native physical
coordinates remain in assembly/pcba-r01/cpl.csv and the current placement SVG.
Factory machine datums must be confirmed; do not blindly mix these coordinate sets.

IMPORTANT OPEN ITEMS:
  Read assembly/pcba-r03/smt-disposition.md and smt-report.pdf.
  Actual SMT analysis has unresolved pin-edge, paste-overlap and board-edge findings.
  Some returned categories are truncated at 50 results; no complete SMT pass exists.
  J6 exact part/land/net checks exist, but visual model and explicit SMT pin coverage
  are incomplete. The backend reports its body spacing; that is narrower evidence.

Design stack: six-layer JLC06081H-7628, 0.8mm class, CAD 0.84088mm.
DFM quote defaults (1.6mm/generic finish/copper) are not order instructions.
C11/C12 are DNP. J3/J4/J5/J7 are bare interfaces, not missing SMT components.
The manufacturer must fit all 81 BOM references; Q1 and J6 must not be omitted.

All source and check artifacts in this package are for review. No order, supplier
message, production programming, powered device test or ingress test was made.
The broader no-user-soldering delivery requirements are in docs/pcba-delivery.md.
