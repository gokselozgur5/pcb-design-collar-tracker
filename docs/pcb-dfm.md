# PCB / DFM review

This is the historical 30 × 22 mm / 0.2.1 implementation record and its electrical/RF
limits. The later **0.3 / 35 × 28 mm** trial has a [separate report](size-trial-35x28.md)
and [Gerber ZIP](../release/collar-tracker-0.3-35x28-dfm.zip). Its local checks
initially preceded supplier analysis. For the latest released DFM result and active
revision, use [STATUS](STATUS.md).

The owner requested native KiCad source and an uploadable Gerber ZIP generated with
the Python API, as on the earlier GIMP board. Tools: `pcbnew` 10.0.7 and local
Freerouting 2.4.1. Input: the actual KiCad XML netlist.

Package: `release/collar-tracker-0.2.1-dfm.zip`. Final native DRC: 0 errors, 0 opens,
0 parity issues, with 43 library-mismatch warnings from local silk/mask changes.
Gerber outline: 30 × 22 mm; Excellon: 75 plated holes of 0.20 mm. The old 0.2 ZIP
is preserved. The second actual JLC report for 0.2.1 retained 2 Danger / 306 Warning.
Red mask-bridge and silk-clearance findings closed; two red pad-spacing findings
remained. Supplier DFM was not clean. Native DRC is not manufacturing approval;
see [the report review](jlc-dfm-review.md).

The board has four copper layers, target thickness 0.8 mm and 53 footprints.
J3/J4 are charger/battery solder pads, J5 digital heart-rate expansion contacts,
J6 external SIM contacts and J7 1.8 V debug contacts. No actual eSIM or heart-rate
sensor is fitted. Small parts also occupy the bottom; the old mechanical study
has not been reintegrated with this real PCB.

Signals: nominal 0.15 mm, narrow pad escapes ≥0.10 mm. Power class: nominal 0.30 mm.
Clearance 0.10 mm, vias 0.45/0.20 mm, hole-to-copper 0.20 mm, edge-to-copper 0.30 mm.
The initial 0.15 mm minimum target became 0.10 mm for narrow escapes, within the
cited [JLC 1 oz multilayer capability](https://jlcpcb.com/capabilities/pcb-capabilities).
This does not qualify current capacity, voltage drop or RF. Some manually completed
power traces are 0.15 mm; the netclass setting does not prove 0.30 mm throughout.
All four layers contain traces and GND fill; inner layers are not uninterrupted
RF references. Power/RF review remains open.

Before ordering: hardware UVLO, VDD_GPIO sequencing, input protection, battery/NTC,
physical SIM/operator profile, heart-rate method, antennas, RF/laminate stack,
stencil/assembly and physical testing.

Nordic DK package 1.0.0, PCA10171 board 1.0.1 / `400797.PcbDoc`, was inspected with
KiCad's Altium importer. Source-package SHA256:
`535974f95549ea418a6004861a7b2c3daa47606082e5b5d106d35012283f1af3`.
SKY65943's footprint came from it; Skyworks 204404H page 9 was also viewed. Center
mask and three paste windows are separate graphics. In 0.2.1 the center pad became
copper-only while preserving those openings, replacing invalid negative margins.
Assembly review remains open.

BQ25185 uses KiCad's Texas DLH0010A footprint; LIS2DW12 uses LGA-12 2×2 mm.
All 112 nRF community-footprint pin positions/sizes matched the DK comparison;
pin 1's pad/custom-shape representation still needs reconciliation with the current
manufacturer drawing. Raw data: `evidence/nordic-reference-footprints.json`.

`build_draft.py` overwrites the schematic; `build_pcb.py` overwrites placement.
The initial schematic is preserved in `snapshots/pre-pcb-20261024/`.
`scripts/import_route.py` imports a selected SES and compares pad placements with
the source. `scripts/export_dfm.py` blocks normal export on DRC errors or opens.
Read the actual final DRC and package manifest together; this document alone is
not a test result.

The final route came from `build/pcb/collar-r6.ses`. `scripts/finish_pcb.py` completed
five remaining connections and the CHG_FAULT route around BAT. Two new vias wholly
inside existing same-net via copper were then removed; final DRC confirmed
connectivity. Intermediate evidence: `evidence/local-routing-fixes.json`,
`evidence/pcb-finished-drc.json`, `build/pcb/pre-via-cleanup.kicad_pcb`.
Rerunning generators overwrites manually completed routing. Re-exporting the existing
package only needs `python3 scripts/export_dfm.py`.

For 0.2.1, `fix_jlc_dfm.py`, `place_dfm_labels.py` and `apply_dfm_labels.py` apply
deterministic corrections to the old source copy. Shapely 2.1.2 runs only in
`.venv-dfm` geometry checks. Export runs the before/after geometry check and native
DRC before packaging.

The owner uploaded the first package to JLCDFM. At this historical stage the
assistant had not uploaded files, ordered hardware or performed physical tests.
