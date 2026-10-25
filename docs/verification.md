# Initial schematic verification — 2026-10-24

This records the draft schematic's check scope. It is not production approval.

## Passed checks

- KiCad 10.0.7 opened the schematic and exported PDF and XML netlist.
- Default ERC: 0 errors / 0 warnings / 0 excluded violations. No project suppression.
  Four default-ignored checks remain explicit in `evidence/erc.json` under
  `ignored_checks`: single global label, four-way junction, SPICE model, footprint filter.
- 18 checks passed against actual KiCad XML: 113 nRF pins, 30 GND pins, 27 separately
  unconnected reserved pins, separate SIM supply, reset/DEC0, RF-port separation,
  LNA link, charger settings, motion sensor and experimental sensor interface.
- Candidate nRF footprint contains pin numbers 1–113 exactly once. This verifies
  pin coverage, not pad coordinates.
- The PDF was visually inspected: five sections and open-design notes fit the A2
  sheet, which requires zooming for screen reading.

Initial drawing-grid and library-definition ERC issues were corrected. Power flags
describe the external 5 V/GND source and supply continuity after the ferrite; they
do not validate missing UVLO or startup sequencing.

## Open items at this stage

| Item | State |
|---|---|
| PCB placement/routing/layers/DRC | Subsequent work recorded in `docs/pcb-dfm.md` and separate PCB reports |
| Physical SIM, charger, battery, sensor and debug connections | Contact/solder pads exist; actual SIM and heart-rate module unselected |
| U2 / U3 / U5 footprints | Assigned in the DFM draft |
| nRF footprint geometry/paste | Third-party candidate; manufacturer-drawing verification required |
| Hardware low-battery shutdown | Not designed |
| VDD_GPIO startup/shutdown sequencing | Unresolved |
| Input/ESD protection, cell/NTC values | Complete against selected parts/cell |
| RF, antennas, enclosure/body effects | Unmeasured |
| Turkish LTE-M/SIM service compatibility | Account/profile/coverage unverified |
| Heart-rate sensor/contact | Unselected; digital experiment interface only |

100 mA / 4.2 V charging and 500 mA input limit are draft settings, not approved for
a selected cell. Runtime, total mass, board size and cost were not measured in this
schematic check.

## Reproduction

From the project root, with GOKSSD mounted and local KiCad installed:

```sh
scripts/kicad-cli sch erc --format json --severity-all --exit-code-violations \
  --output evidence/erc.json hardware/collar-tracker.kicad_sch
scripts/kicad-cli sch export netlist --format kicadxml \
  --output evidence/collar-tracker.xml hardware/collar-tracker.kicad_sch
/usr/bin/python3 scripts/verify_draft.py
scripts/kicad-cli sch export pdf \
  --output previews/collar-tracker-schematic.pdf hardware/collar-tracker.kicad_sch
```

Details and SHA-256 hashes are in `evidence/connectivity-checks.json`. No physical
hardware or circuit simulation was run. This report covers schematic checks only;
PCB/Gerber work is recorded separately in `docs/pcb-dfm.md` and package manifests.
