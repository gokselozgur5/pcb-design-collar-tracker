# 0.3.2 — U2 manufacturer mask dimensions — 2026-10-25

The actual JLCDFM result for 0.3.1 was 0 Danger / 45 Warning, down from 67 warnings.
Negative mask: 22 → 2; compound mask: 2 → 0. Pad spacing 10, mask bridge 30 and
mask-to-trace 3 were unchanged. The source PDF and five images are stored locally
under `evidence/jlc-dfm-20261025-r5`. SMT analysis was disabled.

This report records the initial 0.3.2 delivery state: **no supplier result yet**,
no claim of closing all 45 warnings or production approval. No new placement
finding required a larger board. See [0.3.3](clearance-revision-0.3.3.md) for the
later actual 0.3.2 supplier result.

## Justified change

Downloaded and visually inspected Figure 7 / page 9 of
[SKY65943-11, Skyworks 204404H](https://www.skyworksinc.com/-/media/C1965FC4C165469FAEED1BA276874AF1.pdf),
dated 2025-09-04. Local source: `references/dfm-r5/SKY65943-11-204404H.pdf`.

| U2 mask opening | 0.3.1 | 0.3.2 |
|---|---|---|
| Center, pad 11 | 1.55 × 2.487 mm | 1.55 × 2.90 mm |
| Four large outer pads: 1, 5, 6, 10 | 0.525 × 0.615 mm, r=0.05 corners | 0.525 × 0.515 mm, rectangular |
| Six small outer pads | 0.525 × 0.375 mm | Unchanged |

The manufacturer permits 60–100% of the illustrated center opening; this candidate
uses full size. The earlier partial coverage was therefore not classified as a
proven assembly defect by itself. Four outer-mask Y dimensions now match Figure 7.
Copper was not shrunk and paste was not enlarged. Center opening area increased
0.64015 mm²; outer openings decreased by a total 0.2014145 mm². The bottom revision
label became `COLLAR 0.3.2 TEST`.

## Verification

- Native DRC: 0 errors, 0 opens, 0 schematic mismatches; 47 library-footprint
  warnings retained. No rule/severity/exclusion changes.
- 53 footprints, 792 segments, 77 vias of 0.60/0.20 mm; 35 × 28 × 0.8 mm,
  four copper layers, with In1 dedicated to GND.
- Native comparison confirmed identical copper pad shapes/positions, tracks,
  vias and zone settings. Identity-based matching distinguishes U.FL ground pads
  that share a pin number.
- Four copper, two paste, bottom mask and outline Gerbers are byte-identical after
  removing date/revision metadata. Other parts' top masks are unchanged. Top silk
  remains empty despite changed negative mask commands; bottom silk changes only
  the revision text.
- **All 214 top + 54 bottom = 268 pads are fully exposed.** U2.11's partial coverage
  is gone, improving 267/268 to 268/268. This does not prove every JLC negative-mask
  criterion or closure of its two warnings.
- Minimum separate mask bridge: 0.125 mm, none below 0.10 mm. Changed openings to
  foreign-net pad/trace/via clearance: minimum 0.1735 mm. This excludes same-net
  fill/neck geometry.
- Top/bottom previews, outline, 77 holes, ZIP CRC and all package hashes checked.
  Previous sources and ZIPs preserved.

Verification was corrected to use pad identity rather than duplicate pin numbers,
include the empty top-silk negative commands and account for old rounded mask
corners. Initial `FromMM` truncation left two polygon corners short by 1 nm;
rounding fixed them. Final source and Gerber checks passed on the corrected version.

## Remaining supplier findings at delivery

Copper-image matching (0.920) and visual comparison located the 0.08 mm mask/trace
example at U1.71's ground neck. This was not shown to be a gap between different
nets. Supplier measurement rules and the other two examples were unknown, so the
category stayed open and the area was unchanged. Two negative-mask warnings could
not be reliably located. A later supplier report was needed to assess the U2 change.

0.3.1 had 18 U2 and 12 U5 mask-neighbor gaps below 0.20 mm. Their total matches the
30 warnings, but no occurrence IDs establish correspondence. U5 pads were not
shrunk just to clear the report at this stage: the
[LIS2DW12 package drawing](https://www.st.com.cn/resource/en/datasheet/lis2dw12.pdf)
and [ST TN0018](https://www.st.com/resource/en/technical_note/cd00134799.pdf)
support the existing 0.375 × 0.35 mm land. Process review continued. Comparing JLC
limits is not order-specific fabrication/assembly approval.

U1 mask/stencil, exact BOM, power/UVLO/VDD_GPIO, battery/NTC/ESD, RF/stackup/antennas,
physical SIM/operator, firmware/fixture/test and enclosure remain open. The target
is working factory delivery without user soldering. This is a DFM trial package,
not a working product or order-ready PCBA.

## Delivery and reproduction

ZIP: `/Users/gok/codex/projects/collar-tracker/release/collar-tracker-0.3.2-35x28-dfm.zip`

SHA256: `c09893e5c211a3e98fdaba4b1ae3fafa7e17e737543e1a02530f64e386254d04`

Source: `/Users/gok/codex/projects/collar-tracker/experiments/35x28-mask-r032/hardware/collar-tracker.kicad_pcb`

PCB SHA256: `4dbc5ce1fe08628c8239f155c70aed1a46200ec83cbfd1dc0b765716c79e0b18`

139838 bytes, 20 files. Evidence: `experiments/35x28-mask-r032/evidence/`.
Sequence: `revise_mask_032.py` (KiCad Python; refuses an existing trial),
`dfm_geometry.py`, `check_size_trial.py --mask-revision-032` (geometry venv),
`export_mask_revision032.py`, `audit_release_mask.py`, `verify_mask_revision032.py`.
Export does not overwrite the ZIP. New changes require a separate revision.
No order, external upload, supplier message or physical test occurred at this stage.
