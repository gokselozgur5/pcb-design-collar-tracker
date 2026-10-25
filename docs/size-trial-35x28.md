# 35 × 28 mm trial — 0.3 — 2026-10-24

The 35 × 28 mm board passed local connectivity and geometry checks. These results
did not justify growing to 40 × 30 mm yet. The actual JLCDFM report dated
2026-10-24 21:45:56 returned 0 Danger / 67 Warning. SMT analysis was disabled;
electrical/RF/assembly review remained open.

| Check | Result |
|---|---:|
| Actual Gerber outline | 35 × 28 mm |
| Layers / footprints | 4 / 53 |
| KiCad errors / opens / parity issues | 0 / 0 / 0 |
| Footprint-library warnings | 43 |
| Minimum drawn track width | 0.20 mm |
| Ground-fill minimum width setting | 0.20 mm |
| Via copper / drill / nominal ring | 0.60 / 0.20 / 0.20 mm |
| Actual Excellon plated-hole count | 77 |
| Pad bounding box → via copper, all nets | ≥0.20 mm |
| Pad bounding box → foreign-net trace | ≥0.20 mm |
| Via → via, all nets | ≥0.2026 mm |
| Separate mask bridges below 0.10 mm | 0 |
| Minimum silk → pad/mask / hole | 0.229 / 0.316 mm |
| Gerber layers / ZIP files | 11 / 19 |
| Actual JLC PCB DFM | 0 Danger / 67 Warning |
| SMT analysis / physical test | Not performed / not performed |

Area increased from 660 mm² (30 × 22 mm) to 980 mm², +48.5%. Previous minimum
track width was 0.10 mm and via ring 0.125 mm. Both supplier pad-spacing Danger
findings fell to zero in the new report. The local pad-corner check is not a copy
of JLC's algorithm; the actual new report proves their closure. Remaining categories
and independent Gerber review are in [DFM reports](jlc-dfm-review.md).
The ZIP's NOT RUN note describes packaging time; the delivered ZIP was not altered.

The first attempt with both inner layers dedicated to GND did not close every net.
The passing candidate has no signal traces on In1; In2 carries 116 signal/power
segments plus GND fill. Total: 792 segments. RF impedance, antennas, return paths
and electromagnetic performance were not qualified.

Placement and routing were rebuilt. Some charger-area GND tracks were removed and
reconnected through fill and additional ground vias. Final checks show all nets
connected. Copper-pad shapes, net mapping and masks match 0.2.1 apart from placement.
The router used temporary conservative rectangular obstacles; native production
pads were not changed for that purpose.

Twelve fixed-package pad pairs have 0.15–0.18 mm gaps. `collar-tracker.kicad_dru`
applies 0.15 mm only to **two pads in the same footprint**; tracks/vias retain
0.20 mm checks. No general exclusions or severity reductions. The 43 warnings
come from inherited 0.2.1 footprint silk/mask edits. Shared U.FL openings and
nRF footprint/pin-1/stencil still require assembly review. No claim that every
JLC warning would disappear was made.

Source: [`experiments/35x28-in2/hardware/`](../experiments/35x28-in2/hardware/).
[Final DRC](../experiments/35x28-in2/evidence/final-drc.json),
[independent geometry](../experiments/35x28-in2/evidence/geometry-checks.json),
[ZIP/hash manifest](../experiments/35x28-in2/evidence/delivery.json),
[top](../experiments/35x28-in2/previews/final-top.png) and
[bottom](../experiments/35x28-in2/previews/final-bottom.png) previews.
Both sides were inspected. ZIP CRC, internal hashes, PCB hash, outline coordinates
and Excellon hole count were checked.

Package: [`collar-tracker-0.3-35x28-dfm.zip`](../release/collar-tracker-0.3-35x28-dfm.zip).
Re-export: `python3 scripts/export_size_trial.py`. It runs fresh native DRC and
checks the geometry report's source hash, rejecting errors/opens/parity or failed
geometry. After PCB changes, first rerun `dfm_geometry.py` and
`check_size_trial.py experiments/35x28-in2`. `build_size_trial.py --inner2-signal`
only creates initial placement; rerunning it destroys later routing completions.

This is not a physical/powered prototype test. Power/UVLO/VDD_GPIO, battery/NTC/ESD,
physical SIM/operator, heart-rate hardware, antennas/stackup and assembly remain
open. J6 is an external SIM interface; J5 is digital expansion. The old 38 × 30 mm
enclosure was not revalidated. At this stage no order or assistant supplier upload
occurred. Earlier 0.2/0.2.1 ZIPs and legacy `hardware/` source were preserved.
