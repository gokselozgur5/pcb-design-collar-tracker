# PCB Design: Collar Tracker

A small GPS and cellular tracker for dog collars, starting with Türkiye.
The aim is one electronics design with different collar mounts. Fit, weight and
comfort across dog sizes and coat types still need physical validation.

**The current r05k PCB passed two actual JLC PCB DFM analyses at 0 Danger / 0 Warning.**
Both used the same ZIP and unchanged rules: 29 analyzed rows, 450 green measurements
per run. Native DRC/ERC/parity also pass.

The board is 40 × 32 mm with six copper layers and a physical nano-SIM. The RF
candidate uses a documented 7628 stack and 0.36 mm main port routes; In1.Cu and
In4.Cu remain dedicated GND. All 128 signal vias pass the local return screen.

[Gerber ZIP](experiments/power-r05k-selected-parts/evidence/collar-tracker-05k-parts-40x32-dfm.zip) ·
[Current review PDF](release/r05k-review/review.pdf) ·
[PCB review bundle](release/collar-tracker-r05k-pcb-review.zip) ·
[R3 before / after](experiments/power-r05j-rf-junctions/evidence/rf-junction-review.pdf) ·
[JLC report 1](experiments/power-r05k-selected-parts/evidence/jlc-check1/report.pdf) ·
[JLC report 2](experiments/power-r05k-selected-parts/evidence/jlc-check2/report.pdf)

R3 now has one equal-width copper entry on each land and nearly equal contour
ratios. The LTE tuning stubs are reduced, with a longer main feed as the tradeoff.

**Electrical, RF and manufacturing release remain on hold.** Supplier stack/etch/mask
confirmation, module-pad qualification, assembly process and powered timing,
pack/NTC, antennas and factory programming/test remain open. See the
[r05k review](experiments/power-r05k-selected-parts/README.md). PCB DFM does not prove a working PCBA.

The [battery review](assembly/pack-charge-r01/README.md) found that a direct
10k/B3435 NTC permits charging at 50°C while the reviewed pack stops at 45°C.
Charge enable is grounded; a cell-temperature interlock is not implemented.
Neither the NTC nor a pack is selected. This does not change the tested Gerber bytes.

All 65 fitted references now have exact candidate MPNs.
[Candidate BOM](experiments/power-r05k-selected-parts/assembly/candidate-bom.csv) and
[CPL](experiments/power-r05k-selected-parts/assembly/candidate-cpl.csv) are exported.
The [power component model](assembly/power-parts-r01/README.md) includes tolerance,
TCR and leakage; its remaining physical assumptions are explicit. Supplier
procurement, rotations and SMT acceptance are still open.

The enclosure's 69 populated envelopes pass the modeled 0.71–0.91 mm board-thickness
interval. IP68 remains a design target, with provisional 2 m fresh-water / 60-minute
conditions. No physical water/dust test is claimed.
[STATUS](docs/STATUS.md) records the exact source and next action.

The earlier r04i PCB and [r02 review bundle](release/collar-tracker-r04i-swim-r02-fit-review.zip)
remain preserved. Upload only the Gerber ZIP to PCB DFM.

## Continue in a new session

Open this repository in Claude Code and ask it to continue.
`CLAUDE.md` loads the project instructions and current state.
All repository and GitHub content is written in English; chat can use another language.

On the existing Mac:

```sh
cd /Users/gok/codex/projects/collar-tracker
claude
```

To check the saved context and baseline evidence:

```sh
python3 scripts/resume.py
```

[Resume commands](docs/RESUME.md) · [Paul / nano-SIM notes](docs/paul-nanosim.md)
· [Work log](docs/WORKLOG.md) · [Reusable PCB Design workflow](docs/PCB_DESIGN.md)

Repository: [gokselozgur5/pcb-design-collar-tracker](https://github.com/gokselozgur5/pcb-design-collar-tracker).
The local directory remains `collar-tracker`.

## Product requirements

- First market: Türkiye. Operator not selected.
  See the [connectivity evidence and prototype check](docs/turkiye-connectivity.md).
- Small PCB, with features added in software where practical. No on-device AI.
- Shared hardware for small and large dogs.
- Heart-rate sensing is requested; the measurement method is not validated.
- Factory assembly, programming and functional testing; avoid user hand soldering.

## What is verified

The initial KiCad schematic in `hardware/` uses the nRF9151 as a candidate.
The modem choice remains conditional on operator LTE-M/NB-IoT service and coverage.
The schematic supports electrical review; it is not proof of a working RF design
or heart-rate sensor.

The **0.3.4 / 35 × 28 mm / four-layer** baseline received **0 Danger / 0 Warning**
in two JLC PCB reports dated 2026-10-25, 06:39:36 and 06:41:25. Native KiCad checks
also reported zero errors, warnings, open connections and schematic mismatches.
The rules were unchanged.

[Gerber/Excellon ZIP](release/collar-tracker-0.3.4-35x28-dfm.zip) ·
[JLC report](release/collar-tracker-0.3.4-jlc-dfm-report.pdf) ·
[Changes and assembly limits](docs/clearance-revision-0.3.4.md)

That board has 53 footprints, 792 track segments and 77 vias of 0.60/0.20 mm.
In1.Cu is a GND reference; In2.Cu also carries signal/power traces.
**SMT assembly is not qualified.**

The [order-readiness review](docs/order-readiness-0.3.4.md) found no open ground
connections across 78 GND pads. However, 52 of 61 non-GND vias fall outside the
historical 2 mm return-via screen, and the second inner layer carries signals.
Power, RF, SIM, BOM and functional-delivery work remain open. **Do not order it as
a finished, working PCBA.**

## Source revisions

- Validated PCB DFM baseline: `experiments/35x28-clearance-r034/hardware/`.
- Preserved 35 × 28 mm checkpoint: `experiments/paul-nanosim-r04e/hardware/`.
- Current six-layer PCB: `experiments/power-r05j-rf-junctions/`.
- Preserved six-layer baselines: `experiments/power-r05i-rf-stack/` and `experiments/power-r05h-six-layer/`.
- Preserved four-layer nano-SIM PCB: `experiments/paul-nanosim-r04i-sim-access-40x32/`.
- Preserved 40 × 32 mm DFM checkpoint: `experiments/paul-nanosim-r04g-returns-40x32/`.
- Earlier r04 routing and rejected r04c experiment are preserved separately.
- Legacy 30 × 22 mm / 0.2.1 source: `hardware/`, preserved with its original ZIPs.

The second actual JLC report for 0.2.1 had 2 Danger / 306 Warning; those counts do
not describe either newer board. Earlier findings are in
[the DFM review](docs/jlc-dfm-review.md); electrical/RF limits are in
[PCB DFM notes](docs/pcb-dfm.md).

The first mechanical study uses a 30 × 22 mm PCB and has not been revalidated for
either 35 × 28 mm or 40 × 32 mm. Its 250 mAh example targets a 38 × 30 × 14 mm
enclosure, or 14.6 mm including an assumed contact protrusion. Antennas, the heart-rate head and much of
the electronics are reserved volumes, not fitted production components.

The preserved `mechanical/swim-r06-six-layer-fit/` profile is checked against the
current r05j placements and thickness interval in its `evidence/thickness-fit.json`.
Battery capacity, charge interval, position-update rate and final antennas remain open. Earlier cost ranges were estimates, not supplier quotes, and did not
include heart-rate hardware.

## Files

| Path | Purpose |
|---|---|
| `experiments/35x28-clearance-r034/hardware/` | Native source that passed local and JLC PCB DFM checks |
| `experiments/power-r05j-rf-junctions/` | Current six-layer source, final Gerber and two verified JLC passes |
| `experiments/paul-nanosim-r04i-sim-access-40x32/` | Preserved four-layer source and supplier evidence |
| `mechanical/swim-r02-fit/` | Parametric swimming enclosure prototype; physical qualification pending |
| `scripts/finalize_clearance034.py` | Binds source, local checks, JLC reports and the exact delivered ZIP |
| `hardware/` | Legacy KiCad project, PCB, five-section A2 schematic and draft BOM |
| `scripts/build_pcb.py` | Builds the legacy PCB from the real XML netlist |
| `scripts/import_route.py` | Imports the legacy Freerouting SES and fills zones |
| `scripts/export_dfm.py` | Exports the legacy Gerber/Excellon ZIP after DRC |
| `previews/collar-tracker-schematic.pdf` | Zoomable schematic preview |
| `docs/decisions.md` | Decisions, assumptions and open selections |
| `docs/heart-rate.md` | Research and validation scope for canine heart-rate sensing |
| `previews/compact-250-review.png` | Dimensioned mechanical study |
| `mechanical/packing-study.scad` | Editable OpenSCAD volume study |
| `mechanical/compact-250-sizing-dummy.stl` | Solid dummy for size trials only |
| `mechanical/README.md` | Mechanical assumptions, checks and reproduction |
| `references/manifest.json` | Manufacturer document sources and SHA-256 hashes |
| `evidence/` | Selected CAD checks and pin-connectivity evidence |

## Schematic checks and tools

The initial schematic passed 18 checks against its exported netlist and had zero
violations under KiCad 10.0.7's default ERC profile. Four checks ignored by default
are listed in [the verification report](docs/verification.md). This does not
validate RF, power sequencing, battery behavior or heart-rate measurement.

KiCad 10.0.7 is installed in the workspace on GOKSSD; the system Applications
folder was not changed. `scripts/kicad-cli` and `scripts/kicad-python` are local
entry points. See [RESUME](docs/RESUME.md) for environment overrides.

`scripts/build_draft.py` regenerates the legacy schematic;
`scripts/verify_draft.py` checks it. Regeneration overwrites the schematic, so do
not run it over manual edits. The Nordic footprint source, commit and license are
recorded in `hardware/NORDIC_LIBRARY_NOTICE.txt`. Regeneration needs that source
under `references/nordic-lib-kicad`; the saved native schematic opens independently.
