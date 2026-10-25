# 0.3.1 — measured mask/pad revision — 2026-10-25

Later validation: the JLCDFM report dated 2026-10-25 01:28:03 returned
**0 Danger / 45 Warning** for this revision. Negative-mask warnings fell 22 → 2,
compound-mask warnings 2 → 0; the other categories stayed at 10/30/3. SMT disabled.
Local evidence: `evidence/jlc-dfm-20261025-r5`; next candidate:
[0.3.2](mask-revision-0.3.2.md). The original ZIP remains unchanged.

The rest of this report records the initial delivery state. The latest user report
then covered `collar-tracker-0.3-35x28-dfm.zip`, dated 2026-10-25 00:42:22, again
**0 Danger / 67 Warning**. The previous turn had not changed 0.3. A separate 0.3.1
source and ZIP were created. **At delivery, 0.3.1 had no supplier DFM result and
no zero-warning claim.**

| Change | Before | Measured in 0.3.1 |
|---|---:|---:|
| C1/C2/C5/C8 copper pad spacing | 0.18 mm | 0.25 mm |
| Same components' mask bridge | 0.18 mm | 0.20 mm |
| J3–J7 contact-pad mask expansion | 0 | 0.05 mm |
| Shapes making each J1/J2 shared mask opening | 4 | 1 |
| U2.1 mask → GNSS_LNA_EN control trace | 0.1517 mm | 0.2100 mm |
| Ground-zone clearance setting | 0.20 mm | 0.25 mm |

Four 0201 capacitors use 0.30 × 0.35 mm pads at 0.55 mm pitch; pads moved inward
0.045 mm. Separate paste-only pads were matched in shape and center. Mask expansion
is +0.025 mm. These dimensions fall within the common GRM03 / 0.6 × 0.3 mm ranges
in [Murata's GRM family reference](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM0115C1C100GE01-01A-EN_PDF_CERAMICCAPACITORSMD?lastModifiedDatetime=20250813132738):
a=0.25, b=0.30, c=0.35 mm. This is a family-guide-compatible reflow candidate;
exact ordering codes, tolerances and assembly review remain open.

U.FL openings were merged from the previous delivery's actual Gerber. Copper,
paste and physical copper keepouts were preserved. One polygon alone did not prove
closure of JLC's compound-mask warning. Including arc approximation, boundary error
is below 0.00002 mm. Old native KiCad polygons differed by about 0.0074 mm at these
corners, so the comparison used actual Gerber openings.

Only three GNSS_LNA_EN control-trace endpoints changed. RF, other traces, net
mapping and all 77 vias were preserved. Ground zones were refilled at 0.25 mm
clearance and connectivity rechecked. Two bottom labels moved 0.10 mm; the board
reads `COLLAR 0.3.1 TEST`.

## Verification

- Native KiCad: 0 errors, 0 opens, 0 schematic mismatches; 47 footprint-library
  warnings explicitly retained. No severity/exclusion changes.
- 53 footprints / 792 segments / 77 vias; 35 × 28 × 0.8 mm, four copper layers.
- Pad bounding box to via/foreign-net trace ≥0.20 mm; via-to-via ≥0.2026 mm.
- Native/actual-Gerber comparison found no separate mask bridge below 0.10 mm.
- Independently measured the four capacitors' Gerber copper/mask gaps and paste
  matches. All unspecified pad copper remained unchanged.
- Of 214 top + 54 bottom pads, 267 were fully exposed. U2.11's DK-derived center
  pad retained partial mask coverage. This did not prove closure of all 22 JLC
  negative-mask warnings.
- Checked outline, 77 holes of 0.20 mm, ZIP CRC and all internal file hashes.
  Previous 0.3 PCB/ZIP and 0.2.1 / 30 × 22 mm source stayed unchanged.
- Inspected top/bottom native copper and silk previews. No physical/powered test.

## Open items at delivery

U5's fixed 0.15 mm pad gaps, U2's 0.125–0.1485 mm mask gaps, U2 center mask and
nRF lands/masks still needed review. The [JLC capability table](https://jlcpcb.com/capabilities/pcb-capabilities)
listed 0.15 mm for different-net SMD pads and 0.10 mm mask bridges with colored
mask/1 oz copper; some generic warnings may fall within those limits. This does
not replace process/color/copper-specific fabrication and assembly acceptance.

U1's 1:1 paste output stayed unchanged.
[Nordic](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html)
describes supplying 1:1 paste data for the assembler to adapt. The file alone is
therefore not a proven defect; the final stencil still needs assembler agreement.
Separate area-reduction guidance applies when preparing a stencil without that
input. This revision does not approve stencil manufacture.

The target remains factory-delivered working hardware without user soldering.
BOM, physical SIM/battery/antenna, sequencing/UVLO/ESD, RF/stackup, firmware, fixture
and functional tests remain open. This is a DFM review package.

## Files and reproduction

ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.1-35x28-dfm.zip`

Source: `/Users/gok/codex/projects/collar-tracker/experiments/35x28-mask-r031/hardware/collar-tracker.kicad_pcb`

Evidence in that trial's `evidence/`: `final-drc.json`, `geometry-checks.json`,
`gerber-mask-audit.json`, `gerber-revision-checks.json`, `changes.json`, `delivery.json`.

Sequence: `revise_mask_031.py plan` (geometry venv), `apply` (KiCad Python),
`dfm_geometry.py`, `size_trial_labels.py` plan/apply, geometry again,
`check_size_trial.py --mask-revision-031`, `export_mask_revision.py`, Gerber audits.
Apply starts from 0.3; do not run it over later manual edits. Export refuses to
overwrite the existing 0.3.1 ZIP. Further changes require a new revision.
