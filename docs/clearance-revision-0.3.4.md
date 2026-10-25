# 0.3.4 — U1.71 ground connection

The first JLC record for 0.3.3 showed 0/0. The owner's screenshot and a fresh
upload of the delivered ZIP showed **0 Danger / 1 Warning**. Accepting one zero
result as completion was insufficient. The previous PDF/ZIP were preserved;
`release/collar-tracker-0.3.3-recheck.json` records the contradictory observation.
The cause of different results for identical ZIP bytes is not established.

## Fix

Raw coordinates from the repeat analysis located the remaining 0.080419 mm gap
at **U1.71**. U1.30 and U1.71 are symmetric but separate connections; identifying
U1.30 earlier did not prove U1.71 was clean.

Widened only one U1.71 GND segment from **0.20 to 0.30 mm**. Endpoints, net and
layer stayed unchanged. Pads, masks, paste, components, vias/holes and checking
rules were preserved. Ground zones were refilled; revision label/title became 0.3.4.

`scripts/verify_clearance034.py` uses the actual JLC measurement span: 0.080419 mm
lies outside the old trace, while the new GND copper covers the complete span.
This gives a regression that rejects the old geometry and passes the fix.
Native KiCad, all severities/tracks/parity: **0 errors / 0 warnings / 0 opens /
0 parity issues**. In1/In2/B.Cu, both mask/paste layers, drills and outline outputs
are identical apart from date/revision metadata.

## Evidence and delivery

**Two independent uploads returned 0 Danger / 0 Warning.** Reports are dated
2026-10-25 06:39:36 and 06:41:25; PCB enabled, SMT disabled. Both PDFs were viewed
in full. The second upload used the final delivery path; the ZIP was not rebuilt
or changed afterward.

- [First JLC record](https://jlcdfm.com/viewer?pcbUploadFileId=637107561329414146)
- [Second JLC record](https://jlcdfm.com/viewer?pcbUploadFileId=637107883633496065)
- ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.4-35x28-dfm.zip`
- Final PDF: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.4-jlc-dfm-report.pdf`
- Machine-checked delivery: `release/collar-tracker-0.3.4-verification.json`
- Source: `experiments/35x28-clearance-r034/hardware/`
- Local checks: `experiments/35x28-clearance-r034/evidence/local-checks.json`
- Portable JLC evidence: `evidence/release-034/check1/` and `check2/`
- Original local captures: `evidence/zero-warning-r033/candidate034-check1/` and `candidate034-check2/`
- ZIP SHA256: `735ff8506629eb931cdd4a1847796e0eae2ec24deebb4f579f7441bb2182c990`
- PCB SHA256: `597ebdee59550b6d07eb104274eabee57b038ea6c87da2dec38c1201f78c89b2`

ZIP: 132624 bytes, 14 files. Final PDF SHA256:
`d85511db1fd7d8b826c86be4ad319612ad53d5e809f8e5eda46b0aadb886d7c8`.
Unchanged JLC rules SHA256:
`f1bebb3b2b5ac2ba0579f882fc0605d169c1d6a3a852a07beb8652b719e0a725`.

`scripts/finalize_clearance034.py` requires two different JLC record IDs, identical
upload hashes, all 29 rows analyzed, zero red/orange results, unchanged rules and
raw measurements. The browser helper follows only the new upload's ID and waits
for all rows to remain stable across two consecutive reads.

This work covers PCB DFM. SMT qualification of the 0.3.3 U5 land/U2 mask process
adaptations and electrical/RF/BOM/SIM/firmware/fixture/enclosure requirements remain
open. It is not acceptance of a working PCBA.
