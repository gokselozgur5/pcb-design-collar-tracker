# Current state — 2026-10-25

**Active: Paul layout fixes + physical nano-SIM + real JLC DFM all green.**

Repository: `gokselozgur5/pcb-design-collar-tracker`, public. The local directory
remains `/Users/gok/codex/projects/collar-tracker`. All repository/GitHub content
must be English. Publication is a checkpoint; the new revision is unfinished.

| Item | State | Evidence/source |
|---|---|---|
| Last accepted PCB DFM baseline | 0.3.4, 35 × 28 × 0.8 mm, four copper layers | `experiments/35x28-clearance-r034/hardware/` |
| Baseline validation | Native DRC/ERC clean under recorded profile; two JLC PCB runs 0/0 | `evidence/release-034/`, `release/` |
| Production readiness | Open power/RF/BOM/SMT/firmware/fixture/mechanics | `docs/order-readiness-0.3.4.md` |
| New revision | 54 footprints; nano-SIM socket + ESD; native PCB saved | `experiments/paul-nanosim-r04/hardware/` |
| Ground-only stage | 81 GND pads, 68 local GND vias; both inner planes filled; zero GND opens | Trial `evidence/ground-plan.json`, `ground-applied.json`, `ground-drc.json` |
| Ground-stage native DRC | 0 violations / 0 parity issues / 84 non-GND opens | Trial `evidence/ground-drc.json` |
| First route imported | 14 opens / 3 dangling vias / 0 parity issues; no inner traces | Trial `evidence/routed-1-drc.json`, `routed-1-import.json` |
| New revision JLC DFM | Not run | Baseline acceptance does not transfer |

## Exact next action

Finish the remaining routing from the current r04 PCB, using the actual coordinates
in `evidence/routed-1-drc.json`. Resolve 14 open connections and three dangling vias.
Before adapting the old completion helper, add footprint-zone keepouts and appropriate
power widths; its existing board-zone-only / fixed-0.2-mm assumptions are insufficient.

The builder's SWIG removal failure is resolved: snapshot items before mutation and
use `Delete`. **Do not rerun it over the existing r04 board.** Use a new `--name`
for any placement reproduction. `build/ground-base.kicad_pcb` preserves the ground
stage; `build/routed-1.ses` preserves the first router result.

The first router completed with 19 opens / 12 router violations. Native import
preserved 190 GND items, restored all 24 original RF segments exactly, and widened
three sub-0.20 mm segments to 0.20 mm. The actual native result is reported above.
These checks do not qualify power, RF or complete routing.

Current imported PCB SHA256:
`f225195ee9a4e6b0f508f8fd2e578679c09bd7a38e89e916c5a9fb433f5718c2`.

Then complete:

1. Review socket/ESD pin mapping, land geometry, bottom keepouts and card access.
2. Finish outer-layer signal/power routing while preserving local GND and RF geometry.
3. Add return vias; review actual power widths, passive copper balance and labels.
4. Verify native DRC/ERC/parity, grounds, actual fills and physical geometry.
5. Export new Gerbers; run JLC twice with unchanged rules and identical final bytes.
6. Bind evidence to source/ZIP hashes, update STATUS and deliver the absolute path.

## Fixed decisions and limits

Nano-SIM now, eSIM later. Socket: **GCT SIM8051-6-0-14-00-A / C7363812**;
ESD: **TI TPD4E1U06DCKR / C194628**. D5 and D6 socket drawings were visually
inspected; source hashes are in `references/paul-nanosim-r04/sources.json`.
Factory stock/assembly acceptance is still open.

nRF9151 uses LTE-M/NB-IoT and a 1.8 V UICC. Turkish operator/service/mobility
qualification remains open; a regular phone SIM does not establish compatibility.
J5 remains a digital expansion port, not a heart-rate sensor.

0.3.4 has one signal-free inner plane; 52 of its 61 non-GND vias are outside the
historical 2 mm return screen, maximum 7.0902 mm. This is a review gap, not 52
experimentally demonstrated failures. Its green DFM does not close Paul's feedback.

No order, payment, supplier message, powered test or production approval has occurred.
