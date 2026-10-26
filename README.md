# PCB Design: Collar Tracker

A small GPS and cellular tracker for dog collars, starting with Türkiye.
The aim is one electronics design with different collar mounts. Fit, weight and
comfort across dog sizes and coat types still need physical validation.

**The r05l PCB passed two actual JLC PCB DFM analyses: 0 Danger / 0 Warning / 455 Good each.**
Both used the same ZIP and unchanged rules, with all 29 rows analyzed. Native
DRC/ERC/connectivity/parity have zero findings.

The 40 × 32mm, six-layer nano-SIM board now implements a hardware hot/cold charging
interlock independent of the MCU. Original component lands, placements and RF
segments are preserved. The board has 87 footprints, including 81 fitted references
with 44 exact candidate MPNs. The revised carrier clears the additional components.

[Gerber ZIP](experiments/power-r05l-charge-interlock/evidence/collar-tracker-05l-charge-final4-40x32-dfm.zip) ·
[Latest published four-page review](release/r16-current-review/review.pdf) ·
[Published r16 review bundle](release/collar-tracker-r05l-r16-review.zip) ·
[JLC report 1](experiments/power-r05l-charge-interlock/evidence/jlc-check1/report.pdf) ·
[JLC report 2](experiments/power-r05l-charge-interlock/evidence/jlc-check2/report.pdf)

**Electrical, RF and manufacturing release remain on hold.** The charge model
passes with explicit thermal/leakage assumptions; powered startup and sensor tests
remain open. Protected pack/NTC attachment, antenna qualification, harness/dock/retention,
firmware and factory programming/test are not finished. Supplier procurement, CPL
rotations and SMT acceptance remain open. PCB DFM does not prove a working device.

[Candidate BOM](experiments/power-r05l-charge-interlock/assembly/candidate-bom.csv) ·
[Candidate CPL](experiments/power-r05l-charge-interlock/assembly/candidate-cpl.csv) ·
[Charge review](assembly/charge-interlock-r01/README.md) ·
[r05l source and limits](experiments/power-r05l-charge-interlock/README.md)

The latest [r16 contact retention](mechanical/swim-r16-contact-retention/README.md)
adds rear terminal bearing plates and internal pockets without changing the PCB
or outside size. The [internal harness candidate](assembly/internal-charge-r02/README.md)
now includes both nominal routes and solder-joint envelopes. It remains HOLD:
constant-length movement, restraint and factory joining are unfinished. The
published r16 review archive remains a preserved snapshot.

The [r08 enclosure](mechanical/swim-r08-antennas/README.md) adds CAPH LTE and ZETA
GNSS prototype antennas, two nominal 100mm cable assemblies and four lid guides.
The rigid shell is 57.4 × 49.4 × 20.6mm; the boot is 60.4 × 52.4 × 25.4mm.
All 85 populated envelopes pass four PCB thickness cases. Eight meshes and actual
CAD interference controls are checked. Cable tolerances and assembly forces remain
unqualified. IP68 is a design target with provisional 2m fresh-water / 60-minute
conditions; no physical ingress test is claimed.

The latest [battery request](assembly/pack-r03/README.md) has a
[dimensioned PDF](assembly/pack-r03/request-sheet.pdf) and an unsent supplier enquiry.
Its [r09 fit study](mechanical/swim-r09-pack-request/README.md) includes the pack and
temperature-sensor stack with a 0.4mm height increase. This remains a supplier
request: the existing EEMB 350mA PCM is not approved, and no complete pack is selected.

The preserved [r11 thermal-fit prototype](mechanical/swim-r11-thermal-fit/README.md)
adds four radial keys, larger guide clearances and revised cable paths to the
preserved r10 frame. The [drawing](mechanical/swim-r11-thermal-fit/retention-sheet.pdf)
and saved checks cover 85 component envelopes, 27 cable poses and nine meshes.
Rigid size remains 57.4 x 49.4 x 21.0mm. Material bounds are assigned requirements;
physical thermal fit, connector strain and ingress remain open.

The preserved [r12 pack-retention prototype](mechanical/swim-r12-pack-retention/README.md)
adds a shell-integral cradle and a carrier-integral cap. The requested pack sits
0.3mm lower on the existing floor; outside dimensions are unchanged. The
[review drawing](mechanical/swim-r12-pack-retention/pack-retention-sheet.pdf) and saved
checks cover all 85 components, full upward pack/sensor travel, two changed meshes
and seven CAD controls. Minimum pack size/contact regions, actual strength and
lead routing still require supplier and physical qualification.

The preserved [r13 charging dock](mechanical/swim-r13-charge-dock/README.md) replaces
an empty alignment block with actual spring contacts, flange stops, fuse/wire
space and a jacket-retention bay. Its [drawing](mechanical/swim-r13-charge-dock/dock-sheet.pdf)
and [harness definition](assembly/charge-harness-r01/README.md) identify the pinout,
source dimensions and remaining process gates. The taller external key blocks the
aligned reversed approach before the earliest calculated contact. Holding force,
skewed approaches, power/fault behavior and internal J3 wiring remain unqualified.
The already all-green PCB is unchanged.

The preserved [r14 wire-movement study](mechanical/swim-r14-wire-motion/README.md)
replaces the straight dock pigtails with a constant-length family covering the
full conservative contact movement. Its continuous bend-radius bound is 8.6961mm;
the complete interval envelope clears the new housing and intersects the old one.
The new [r15 wire clamp](mechanical/swim-r15-wire-clamp/README.md) adds a separate
cap, hard stops, four silicone pads and a factory forming fixture. The external
dry dock is 101.5 x 36 x 16mm; the wearable is unchanged. Geometry checks do not
establish grip on PTFE: pad creep, endpoint slip and flex life remain unqualified.
Dock holding, internal J3 wiring, pack approval and physical acceptance are open.
The current review package maps all reused parts to their exact source revisions.

[STATUS](docs/STATUS.md) records the exact source and next action. The earlier r05k,
r04i and all prior tested files remain preserved. Upload only the Gerber ZIP to PCB
DFM; the outer review archive also contains native CAD, assembly candidates and reports.

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
- Current six-layer PCB: `experiments/power-r05l-charge-interlock/`.
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
preserved r05j placements and thickness interval in its `evidence/thickness-fit.json`.
Battery capacity, charge interval, position-update rate and final antennas remain open. Earlier cost ranges were estimates, not supplier quotes, and did not
include heart-rate hardware.

## Files

| Path | Purpose |
|---|---|
| `experiments/35x28-clearance-r034/hardware/` | Native source that passed local and JLC PCB DFM checks |
| `experiments/power-r05l-charge-interlock/` | Current six-layer source, final Gerber and two verified JLC passes |
| `experiments/paul-nanosim-r04i-sim-access-40x32/` | Preserved four-layer source and supplier evidence |
| `mechanical/swim-r08-antennas/` | Current antenna/cable enclosure prototype; physical qualification pending |
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
