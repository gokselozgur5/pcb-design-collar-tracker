# JLCDFM reports and assembly review

## Latest released result — 2026-10-25

**0.3.4: two independent JLC uploads returned 0 Danger / 0 Warning.**
Reports: 06:39:36 and 06:41:25, PCB enabled, SMT disabled. Native KiCad also
reported 0 errors / 0 warnings / 0 opens / 0 parity issues. Rules stayed unchanged.
The final delivery ZIP has the same SHA256 as both report inputs.
Sources and reports: [0.3.4](clearance-revision-0.3.4.md).

The first 0.3.3 report at 06:29:27 showed 0/0; the owner's screenshot and a fresh
upload of the same ZIP showed 0/1. The remaining warning was at U1.71. U1.30 was a
separate symmetric location. Declaring the U1.71 match definitely wrong and closing
the task after one zero result were mistakes. 0.3.4 widens only that U1.71 ground
segment 0.20 → 0.30 mm; pads/masks/paste, other traces, vias, components and rules
are unchanged. A local regression shows the actual JLC measurement span extends
outside the old trace and is fully covered by the new copper. Earlier ZIP/PDF
files and the 0.3.3 repeat-check record are preserved.

## Historical 0.3.1 / 0.3.2 review

Following the request to clear every warning, a separate copy of the same physical
0.3.2 design reduced native footprint warnings **47 → 0**. Customized footprints
were saved in a project library; rules and all 11 Gerber geometries were preserved.
No new JLC result existed at that stage. See [zero-warning work](zero-warning-work.md)
for verification and the actual default 6 mil / 0.1524 mm threshold.

The fifth report, 01:28:03, covered **0.3.1: 0 Danger / 45 Warning**. Of the previous
67 warnings, 22 closed: negative mask 22 → 2, compound mask 2 → 0. Pad spacing
remained 10, mask bridge 30, mask-to-trace 3. The illustrated mask/trace gap was
0.08 mm and negative-mask example 0.04 mm. PCB enabled, SMT disabled. All five
raster sections were inspected; local evidence: `evidence/jlc-dfm-20261025-r5/`.

Copper-image correlation (0.920) plus visual inspection located the 0.08 mm example
at U1.71's ground neck. It was not evidence of insufficient clearance between two
different nets. The category remained open because JLC's criterion and the other
two examples were unresolved. The two negative-mask examples were not reliably
located; low-score matches were not treated as evidence. The PDF lacks complete
occurrence coordinates.

Actual Gerbers had 18 U2 and 12 U5 mask-neighbor gaps below 0.20 mm. Their total
matches 30 warnings, but individual occurrence identities were not established.
At this stage U5 pads were not reduced: the LIS2DW12 package drawing and ST TN0018
supported their dimensions; assembly confirmation remained necessary.

**0.3.2** changed U2 masks to the current Skyworks Figure 7 dimensions, preserving
all copper pads, traces, vias and paste. Local/native/Gerber checks passed; all
268 pads were exposed. See [0.3.2](mask-revision-0.3.2.md). **At that point 0.3.2
had no JLC result; 45 was the 0.3.1 result.** Later actual results are recorded above
and in [0.3.3](clearance-revision-0.3.3.md).

## Fourth report and 0.3.1

The 00:42:22 report again showed 0/67 for the 0.3 ZIP; local evidence:
`evidence/jlc-dfm-20261025-r4/`. The subsequent changes are in
[0.3.1](mask-revision-0.3.1.md). The fifth report measured those changes; the old
ZIP was not delivered again as a new revision.

## Third report: 0.3 / 35 × 28 mm

The complete report dated 2026-10-24 21:45:56 was viewed. Source PDF/images:
`evidence/jlc-dfm-20261024-r3/`. **0 Danger / 67 Warning**; the previous two
pad-spacing Danger findings closed. Four layers and 35 × 28 mm were correct.
**PCB analysis enabled, SMT disabled.** This does not qualify operation or assembly.

| Remaining category | Warnings | Single illustrated example |
|---|---:|---:|
| Pad spacing | 10 | 0.15 mm |
| Mask bridge | 30 | 0.13 mm |
| Mask opening to nearby trace | 3 | 0.15 mm |
| Mask opening made from multiple shapes | 2 | No dimension supplied |
| Negative mask expansion | 22 | 0.04 mm |

The PDF lacks coordinates for every finding. These are not 67 different parts or
67 proven electrical faults. Of the remaining warnings, 57 concern masks and 10
pad spacing; they were not all closed.

### Actual Gerber and native review

- `audit_release_mask.py` read copper, mask and paste from the extracted package
  matching the delivered ZIP, recording layer hashes. Native and Gerber counts
  agree: 214 top + 54 bottom pads. With 0.1 µm comparison tolerance, **267 pads
  are fully exposed**. Only U2.11 is partly covered: copper 1.45 × 2.802 mm,
  separate opening 1.55 × 2.487 mm. This came from the Nordic DK footprint and
  was not automatically classified as correct or defective without assembly review.
- The 22 negative-mask warnings could not be reproduced as 22 undersized openings
  by simple pad-copper/opening comparison. Without the supplier algorithm,
  trace/pad junction rules and all coordinates, they were not dismissed as false
  alarms. Native pad getters had no negative margin; F.Cu/F.Mask expansion values
  were identical.
- Native fixed package gaps: U5 0.15 mm, 0201 capacitors 0.18 mm. A larger board
  does not change them. U2 mask gaps were 0.125 / 0.1485 mm; U5 0.15 mm. No claim
  was made that each matched a specific report occurrence.
- U2.1 mask to GNSS_LNA_EN trace measured 0.1517 mm, a candidate for the category,
  not a mapping of all three findings. This check covered pad masks against
  foreign-net traces, excluding fills and other supplier algorithms.
- J1/J2 had two intentional shared U.FL openings, candidates for the two compound
  mask warnings. Stencil/assembly review remained open.

Evidence: `report-summary.json`, `native-warning-candidates.json`,
`gerber-mask-audit.json`, `pcba-readiness.json`. The reader supports this KiCad
output's R/O/C/RoundRect apertures and linear mask/paste regions, failing on
unsupported formats. Copper pours are not counted as pads. It is not a complete
Gerber DFM engine.

The [JLC capability table](https://jlcpcb.com/capabilities/pcb-capabilities)
listed 0.15 mm different-net SMD spacing, 0.09 mm mask-to-nearby-trace clearance,
and 0.10 mm mask bridges for green/red/yellow/blue/purple with 1 oz copper;
black/white 0.13 mm, 2 oz 0.20 mm. Some orange examples fell within those published
limits. This comparison does not establish selected-stackup/color/process or
assembly acceptance. Shrinking lands just to turn an indicator green was rejected.

### Assembly target and remaining work

The owner requested factory-assembled, programmed, function-tested hardware without
hand soldering. The BOM then had 46 fitted physical parts, 30 lacking exact MPNs,
plus two DNP parts and five PCB contact interfaces. J6 was not an actual eSIM;
J5 was not a heart-rate sensor. Battery/NTC, antennas and external connections
were not fully selected product components.

U1 mask/paste were 1:1 on every pad.
[Nordic's guide](https://docs.nordicsemi.com/r/bundle/nwp_056/page/wp/nwp_056/footprint.html)
recommends NSMD, +0.05 mm mask expansion and assembler input for the stencil.
Without assembler input, it gives roughly 70–80% paste area for large pads and
75–85% for small pads. Full paste area on large pads was not automatically accepted
for assembly. Blanket mask expansion was avoided because it could narrow bridges.

This review did not change the PCB or delivered ZIP, produce new Gerbers or grant
production approval. Next: manufacturer-compatible footprint/mask/stencil review;
complete BOM and connections requiring no user soldering; electrical/RF fixes;
firmware/fixture/test procedure; then PCB and SMT review. See
[factory delivery](pcba-delivery.md).

## Second report: 0.2.1

The complete report dated 2026-10-24 20:41:35 was viewed; source/four images:
`evidence/jlc-dfm-20261024-r2/`. Danger 139 → 2, Warning 325 → 306. Danger categories:
mask bridge 6 → 0, silk-to-pad 98 → 0, silk-to-hole 33 → 0. **Both pad-spacing
Danger findings remained.** Two compound-mask warnings appeared. 0.2.1 was not
fully corrected.

The owner suggested the board might be too small. A 35 × 28 mm first prototype
was proposed: 980 mm² versus 660 mm², +48.5%. At that point the choice between
this, 40 × 30 mm and the current size was unanswered. These are PCB dimensions,
excluding battery, antennas and enclosure. Growth alone cannot solve fixed
package spacing or electrical/RF gaps. No PCB change or new ZIP occurred in that
review. The later 35 × 28 mm trial is documented separately.

Automatic copper-image matching plus visual inspection placed the coordinate-free
pad-spacing example near C6 / SPI_MOSI's via. Actual rounded-pad-to-via clearance
was about 0.1046 mm; pad bounding box to via circle was 0.0468 mm. The latter
matches the illustrated 0.05 mm, but neither JLC's algorithm nor both root causes
was established. Other regions also differed under bounding-box measurement.
This was a candidate/hypothesis, not evidence that JLC was wrong or both errors
were fixed. Evidence: `thumbnail-match.json`, `candidate-0.png`,
`pad-bbox-via-circle.json`.

## First report: 0.2

The supplied `DFM analysis report_JLCDFM_collar-tracker-0.2-dfm.zip.pdf` was viewed
as one long raster page, dated 2026-10-24 20:24:49. Four layers, 3 × 2.2 cm;
PCB DFM enabled, SMT disabled. Source/four readable images:
`evidence/jlc-dfm-20261024/`.

139 Danger and 325 Warning indicators span categories/layers; they do not establish
464 independent circuit faults.

| Category | Danger | Warning | Illustrated value |
|---|---:|---:|---:|
| Track width | 0 | 11 | 0.11 mm |
| Pad spacing | 2 | 45 | 0.05 mm |
| Plated hole to track | 0 | 9 | 0.23 mm |
| Annular ring | 0 | 100 | 0.12 mm |
| Via to pad | 0 | 1 | 0.12 mm |
| Mask bridge | 6 | 30 | 0.01 mm |
| Mask opening to nearby track | 0 | 74 | 0.10 mm |
| Negative mask expansion | 0 | 22 | 0.04 mm |
| Silk to pad | 98 | 0 | 0.09 mm |
| Silk to hole | 33 | 13 | 0 mm |
| Silk line width | 0 | 20 | 0.12 mm |

The initial zero-error KiCad result was not equivalent to this supplier analysis.
Same-net via/pad spacing can escape electrical clearance checks; silk-to-tented-hole
and narrow mask strips need separate geometry checks.

### Corrections and evidence

- Reproduced three 0.01 mm mask strips at each J1/J2 antenna connector from native
  geometry. Added 0.05 mm pad-mask expansion to merge them with the existing center
  opening. Preserved the center copper keepout. Shared mask openings were explicitly
  scoped to these two connectors with `AllowSolderMaskBridges`; no global rule,
  severity or exclusion changes. Assembly/stencil review still applies.
- Moved J4's battery contacts down 0.20 mm: BAT pad/via gap 0.025 → 0.225 mm,
  board-edge clearance 0.50 mm. Via/trace geometry, pad sizes and nets unchanged.
  An earlier via-move attempt failed DRC and is **not** in the delivered version.
- Moved 109 crowded outlines/orientation marks from silk to Fab. Retained board
  and connection labels at 1 mm text / 0.15 mm stroke. Actual glyph polygons gave
  ≥0.249 mm pad/mask clearance, ≥0.311 mm hole clearance and ≥0.30 mm board-edge
  margin for four labels. Small-IC orientation now relies on assembly drawings/CPL,
  not physical silk.
- U2's center mask/paste were already separate graphics. Made the pad copper-only
  instead of using negative margins; preserved separate openings.

`check_dfm_geometry.py` rejects the old six mask strips and close BAT via and passes
the new geometry. Nets, pad sizes, 797 track segments and 75 vias are unchanged;
only J4 placement differs. No separate pad/via gap or mask strip below 0.10 mm
remained in that local check. It does not implement all JLC algorithms. The PDF
lacks all coordinates, so closing both 0.05 mm pad-spacing findings and other
warnings required actual supplier reanalysis.

Final native DRC at this stage: 0 errors, 0 opens, 0 parity issues; 43 local-library
mismatch warnings remained unsuppressed. The package included its DRC summary and
local geometry evidence.

## Interpreting the remaining warnings

The dated [JLC capacity reference](https://jlcpcb.com/capabilities/pcb-capabilities)
listed 0.09 mm track/spacing for 1 oz multilayer boards, 0.20 mm via-hole-to-track
clearance and 0.10 mm colored-mask bridges. The 0.45/0.20 mm vias met the published
via diameter/drill limits; PTH-pad annular rings are a different category. A
0.11 mm track or 0.12 mm ring warning alone did not prove nonmanufacturability.
Tolerances and selected copper/mask/stackup/assembly conditions still needed
confirmation. RF pads and every via were not enlarged just to change indicators.

Production approval remained open: power/UVLO/VDD_GPIO, physical SIM/operator,
heart-rate hardware, antenna/RF/stackup, nRF pin-1 footprint difference, stencil,
bottom-side enclosure fit and physical testing.
